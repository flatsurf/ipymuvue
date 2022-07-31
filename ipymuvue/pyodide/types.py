r"""
Type checks for objects coming out of the Vue.js API.
"""
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

# The interface to JavaScript, only available when running in pyodide.
import js


def is_vue_proxy(x):
    r"""
    Return whether ``x`` is a un unwrapped reactive Vue Proxy.
    """
    import pyodide
    from ipymuvue_js import Vue

    return isinstance(x, pyodide.ffi.JsProxy) and Vue.isProxy(x)


def is_vue_ref(x):
    r"""
    Return whether ``x`` is a un unwrapped reactive Vue Ref.
    """
    import pyodide
    from ipymuvue_js import Vue

    return isinstance(x, pyodide.ffi.JsProxy) and Vue.isRef(x)


# Types for Runtime Type Checks of props
String = js.String
Number = js.Number
Boolean = js.Boolean
Array = js.Array
Object = js.Object
Date = js.Date
Function = js.Function
Symbol = js.Symbol
