r"""
Wrappers for JavaScript arrays.

pyodide wraps JavaScript arrays in a way that is very convenient to
use from Python. However, we want to wrap the entries of that array
with our own object wrapper, see
:module:`ipymuvue.pyodide.proxies.object_wrapper` so we need to
intercept some of the operations on an array.
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

from collections.abc import MutableSequence
from ipymuvue.pyodide.proxies import python_compatible, vue_compatible
from ipymuvue.pyodide.types import is_vue_proxy


class ArrayWrapper(MutableSequence):
    r"""
    Wraps a JavaScript Array with a Python list interface.
    """

    def __init__(self, array):
        import js

        if not js.Array.isArray(array):
            raise TypeError("array must be a JavaScript array")

        self._array = array

    def _vue_compatible(self, object):
        return vue_compatible(object)

    def insert(self, index, object):
        if index < 0:
            index = 0
        if index >= len(self):
            index = len(self)
        self._array.splice(index, 0, self._vue_compatible(object))

    def __getitem__(self, index):
        return python_compatible(self._array[index])

    def __setitem__(self, index, value):
        if index < 0:
            index = len(self) + index
        if index < 0:
            raise IndexError("assignment index out of range")
        if index >= len(self):
            raise IndexError("assignment index out of range")

        self._array[index] = self._vue_compatible(object)

    def __delitem__(self, index):
        if index < 0:
            index = len(self) + index
        if index < 0:
            raise IndexError("deletion index out of range")
        if index >= len(self):
            raise IndexError("deletion index out of range")

        self._array.splice(index, 1)

    def __len__(self):
        return self._array.length


class ProxyList(ArrayWrapper):
    r"""
    Wraps a Vue proxy with a Python list interface.
    """

    def __init__(self, proxy):
        if not is_vue_proxy(proxy):
            raise TypeError("proxy must be a Vue proxy")
        super().__init__(proxy)

    def _vue_compatible(self, object):
        return vue_compatible(object, reference=False)
