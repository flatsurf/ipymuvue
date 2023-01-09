# ******************************************************************************
# Copyright (c) 2022 Julian Rüth <julian.rueth@fsfe.org>
#
# ipymuvue is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ipymuvue is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ipymuvue. If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************


import contextlib
from ipywidgets import DOMWidget, widget_serialization
from ipymuvue.version import __version__ as version
from traitlets import Unicode, List, Dict, Instance


class VueWidget(DOMWidget):
    r"""
    A reactive widget.

    Each output containing this widget renders as a separate Vue app whose
    traitlets are connected to the app's internal state, i.e., its ``data``.

    INPUTS:

    - ``template`` -- a vue.js template string

    - ``capture_output`` -- boolean (default: ``True``) whether to
      display the output of print statements and stack traces of
      exceptions produced by callbacks underneath this widget.

    - ``watch`` -- boolean (default: ``True``) whether to watch ``components``
      and ``assets`` that are backed by files for changes and perform updates
      when they change.

    """

    def __init__(
        self, template, components=None, assets=None, capture_output=True, watch=True
    ):
        super().__init__()

        components = components or {}
        assets = assets or {}

        self.__template = template
        self.__type = type(self).__name__

        self._initialize_components(components, assets)
        self._initialize_assets(assets)

        # Create output area for stdout, stderr, and tracebacks
        from ipywidgets import Output

        self.__output = Output() if capture_output else None

        # Wire up callbacks that can be called from Vue component
        import inspect

        self.__methods = [
            name
            for (name, method) in type(self)._getmembers(self, predicate=inspect.ismethod)
            if hasattr(method, "_VueWidget__is_callback") and method.__is_callback
        ]
        self.__on_msg(self._handle_message)

    @classmethod
    def _getmembers(cls, object, predicate=None):
        r"""
        Return the members of ``object``.

        This code is copied from inspect.getmembers() but adds handling for
        assertion errors. A ipywidget Widget does not like its static methods
        to be inspected from a non-static context so we hack around this
        problem here by ignoring assertions.
        """
        from inspect import isclass
        if isclass(object):
            mro = (object,) + getmro(object)
        else:
            mro = ()
        results = []
        processed = set()
        names = dir(object)
        # :dd any DynamicClassAttributes to the list of names if object is a class;
        # this may result in duplicate entries if, for example, a virtual
        # attribute with the same name as a DynamicClassAttribute exists
        try:
            for base in object.__bases__:
                for k, v in base.__dict__.items():
                    if isinstance(v, types.DynamicClassAttribute):
                        names.append(k)
        except AttributeError:
            pass
        for key in names:
            # First try to get the value via getattr.  Some descriptors don't
            # like calling their __get__ (see bug #1785), so fall back to
            # looking in the __dict__.
            try:
                value = getattr(object, key)
                # handle the duplicate key
                if key in processed:
                    raise AttributeError
            except (AttributeError, AssertionError):
                for base in mro:
                    if key in base.__dict__:
                        value = base.__dict__[key]
                        break
                else:
                    # could be a (currently) missing slot member, or a buggy
                    # __dir__; discard and move on
                    continue
            if not predicate or predicate(value):
                results.append((key, value))
            processed.add(key)
        results.sort(key=lambda pair: pair[0])
        return results

    def _initialize_components(self, components, assets):
        r"""
        Link components to file in assets.
        """
        for (component, definition) in components.items():
            if not isinstance(component, str):
                raise TypeError("component name must be a string")

            if definition in assets:
                continue

            if hasattr(definition, "read") or isinstance(definition, str):
                # Move this component's definition to the assets.
                if hasattr(definition, "name"):
                    import pathlib

                    asset = pathlib.Path(definition.name).name
                else:
                    from uuid import uuid4

                    asset = f"{uuid4()}.vue"

                assets[asset] = definition
                components[component] = asset
                continue

            raise NotImplementedError(
                "cannot process this kind of component definition yet"
            )

        self.__components = components

    def _initialize_assets(self, assets):
        r"""
        Prepare virtual file system for assets.
        """
        import os.path
        import glob

        # Ship ipymuvue to the client (they probably only need the things that are in pyodide/
        for fname in glob.glob(
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "**/*.py"),
            recursive=True,
        ):
            if fname in assets:
                raise ValueError(
                    f"assets must not contain {fname} as it is shipped with ipymuvue"
                )
            assets[
                os.path.relpath(
                    fname,
                    start=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                )
            ] = open(fname, "rb").read()

        for (fname, content) in assets.items():
            if not isinstance(fname, str):
                raise TypeError("file name must be a string")

            if hasattr(content, "read"):
                # Resolve files to their actual content.
                content = content.read()

            if isinstance(content, str):
                content = content.encode("utf-8")

            if not isinstance(content, bytes):
                raise NotImplementedError("assets must be convertible to bytes")

            assets[fname] = content

        self.__assets = assets

    def __getitem__(self, name):
        r"""
        Return a handle for the elements in the frontend marked with
        ``ref="name"`` in the template.
        """
        from ipymuvue.widgets.references import Subcomponent

        return Subcomponent(self, name)

    def slot(self, name, content=None):
        if content is None:
            content = name
            name = "default"

        if not isinstance(name, str):
            raise TypeError("name of slot must be string")

        children = dict(**self.__children)
        children[name] = content
        self.__children = children

    def _repr_mimebundle_(self, **kwargs):
        if self.__output is not None:
            from IPython.display import display

            # This is a hack. We should not call display() in
            # _repr_mimebundle_ but handle everything with _repr_mimebundle_
            # instead (and wrap the output somehow ourselves in the frontend.)
            display(self.__output)

        return super()._repr_mimebundle_(**kwargs)

    @contextlib.contextmanager
    def _on_msg(self, handler):
        r"""
        Register ``handler`` for custom messages from the frontend.

        The handler is unregistered when the context is released.
        """
        logging_handler = self.__on_msg(handler)
        try:
            yield
        finally:
            self.on_msg(logging_handler, remove=True)

    def __on_msg(self, handler):
        r"""
        Register ``handler`` for custom messages from the frontend.
        """
        with (self.__output or contextlib.nullcontext):
            def logging_handler(*args, **kwargs):
                with (self.__output or contextlib.nullcontext):
                    handler(*args, **kwargs)

            self.on_msg(logging_handler)
            return logging_handler

    def _handle_message(self, _, content, __):
        r"""
        Handle a message coming in on the comm from the frontend model.
        """
        if "method" in content:
            with (self.__output or contextlib.nullcontext()):
                self._handle_callback(**content)
                return

    def _handle_callback(self, method, args=()):
        r"""
        Call the method called ``method`` that has been marked as ``callback``
        with ``args``.
        """
        getattr(self, method)(*args)

    @staticmethod
    def callback(method):
        r"""
        Mark ``method`` as a callback that is exposed as ``methods`` in the
        frontend Vue component.
        """
        method.__is_callback = True
        return method

    _model_name = Unicode("VueWidgetModel").tag(sync=True)
    _view_name = Unicode("VueWidgetView").tag(sync=True)
    _view_module = Unicode("ipymuvue").tag(sync=True)
    _model_module = Unicode("ipymuvue").tag(sync=True)
    _view_module_version = Unicode(f"^{version}").tag(sync=True)
    _model_module_version = Unicode(f"^{version}").tag(sync=True)
    __type = Unicode("VueWidget").tag(sync=True)
    __template = Unicode("<div>…</div>").tag(sync=True)
    __methods = List([]).tag(sync=True)
    __components = Dict().tag(sync=True)
    __assets = Dict().tag(sync=True)
    __children = Dict(Instance(DOMWidget), key_trait=Unicode()).tag(
        sync=True, **widget_serialization
    )
