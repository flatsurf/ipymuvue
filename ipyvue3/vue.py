r"""
Helper methods to create Vue components from Python.

This module is automatically provided with the "assets" available when defining
vue components.
"""
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


def define_component():
    import pyodide
    import js

    return pyodide.ffi.to_js({}, dict_converter=js.Object.fromEntries)
