# ******************************************************************************
# Copyright (c) 2022 Julian Rüth <julian.rueth@fsfe.org>
#
# ipyvue3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ipyvue3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ipyvue3. If not, see <https://www.gnu.org/licenses/>.
# ******************************************************************************


from ipywidgets import DOMWidget
from ipyvue3.version import __version__ as version
from traitlets import Unicode, List


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

    """

    def __init__(self, template, capture_output=True):
        super().__init__()

        self.__template = template
        self.__type = type(self).__name__

        import inspect
        self.__methods = [
            name for (name, method) in inspect.getmembers(self, predicate=inspect.ismethod)
            if hasattr(method, '_VueWidget__is_callback') and method.__is_callback]
        self.on_msg(self._handle_event)

        self.__output = None
        if capture_output:
            from ipywidgets import Output
            self.__output = Output()

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
    _view_module = Unicode("ipyvue3").tag(sync=True)
    _model_module = Unicode("ipyvue3").tag(sync=True)
    _view_module_version = Unicode(f"^{version}").tag(sync=True)
    _model_module_version = Unicode(f"^{version}").tag(sync=True)
    __type = Unicode("VueWidget").tag(sync=True)
    __template = Unicode("<div>…</div>").tag(sync=True)
    __methods = List([]).tag(sync=True)
