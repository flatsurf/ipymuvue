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

    def __init__(self, template, components=None, assets=None, capture_output=True, watch=True):
        super().__init__()

        components = components or {}
        assets = assets or {}

        self.__template = template
        self.__type = type(self).__name__

        self._initialize_components(components, assets)
        self._initialize_assets(assets)

        # Wire up callbacks that can be called from Vue component
        import inspect
        self.__methods = [
            name for (name, method) in inspect.getmembers(self, predicate=inspect.ismethod)
            if hasattr(method, '_VueWidget__is_callback') and method.__is_callback]
        self.on_msg(self._handle_event)

        # Create output area for stdout, stderr, and tracebacks
        from ipywidgets import Output
        self.__output = Output() if capture_output else None

    def _initialize_components(self, components, assets):
        r"""
        Link components to file in assets.
        """
        for (component, definition) in components.items():
            if not isinstance(component, str):
                raise TypeError("component name must be a string")

            if definition in assets:
                continue

            if hasattr(definition, 'read') or isinstance(definition, str):
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

            raise NotImplementedError("cannot process this kind of component definition yet")

        self.__components = components

    def _initialize_assets(self, assets):
        r"""
        Prepare virtual file system for assets.
        """
        if "vue.py" not in assets:
            import os.path
            assets["vue.py"] = open(os.path.join(os.path.dirname(__file__), "vue.py"), "rb").read()

        for (fname, content) in assets.items():
            if not isinstance(fname, str):
                raise TypeError("file name must be a string")

            if hasattr(content, 'read'):
                # Resolve files to their actual content.
                content = content.read()

            if isinstance(content, str):
                content = content.encode('utf-8')

            if not isinstance(content, bytes):
                raise NotImplementedError("assets must be convertible to bytes")

            assets[fname] = content

        self.__assets = assets

    def slot(self, name, content=None):
        if content is None:
            content = name
            name = "default"

        if not isinstance(name, str):
            raise TypeError("name of slot must be string")

        children = dict(**self.__children)
        children[name] = content
        self.__children = children

    def _ipython_display_(self):
        if self.__output is not None:
            from IPython.display import display
            display(self.__output)

        return super()._ipython_display_()

    def _handle_event(self, _, content, __):
        from contextlib import nullcontext
        with (self.__output or nullcontext()):
            if 'method' in content:
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
    __children = Dict(Instance(DOMWidget), key_trait=Unicode()).tag(sync=True, **widget_serialization)
