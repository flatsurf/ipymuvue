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
from traitlets import Unicode


class VueWidget(DOMWidget):
    def __init__(self, template):
        super().__init__()

    _model_name = Unicode("VueWidgetModel").tag(sync=True)
    _view_name = Unicode("VueWidgetView").tag(sync=True)
    _view_module = Unicode("ipyvue3").tag(sync=True)
    _model_module = Unicode("ipyvue3").tag(sync=True)
    _view_module_version = Unicode(f"^{version}").tag(sync=True)
    _model_module_version = Unicode(f"^{version}").tag(sync=True)
