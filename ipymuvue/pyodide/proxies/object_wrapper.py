r"""
Wrappers for JavaScript objects.

pyodide wraps JavaScript objects with a PyProxy. However, that proxy does not
provide them with a Python dict like interface that most Python programmers
expect. Here we provide such a wrapper :class:`ObjectWrapper` and a specialized
version, :class:`ProxyDict` that makes sure that no actual Python objects end
up in a Vue proxy without converting them to native JavaScript objects first.
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

from collections.abc import MutableMapping


class ObjectWrapper(MutableMapping):
    r"""
    Wraps a JavaScript object with a Python dict interface.
    """

    def __init__(self, object):
        if not object.typeof == "object":
            raise TypeError("object must be a JavaScript object")

        super().__setattr__("_object", object)

    def _vue_compatible(self, object):
        from ipymuvue.pyodide.proxies import vue_compatible

        return vue_compatible(object)

    def __delitem__(self, key):
        raise Exception("not implemented __delitem__")

    def __getattr__(self, key):
        if not isinstance(key, (int, str)):
            raise TypeError(f"key must be int or str but was {type(key)}")

        from ipymuvue.pyodide.proxies import python_compatible

        return python_compatible(getattr(self._object, str(key)))

    def __setattr__(self, key, value):
        if not isinstance(key, (int, str)):
            raise TypeError(f"key must be int or str but was {type(key)}")

        setattr(self._object, str(key), self._vue_compatible(value))

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __iter__(self):
        import js

        for key in js.Object.keys(self._object):
            yield key

    def __len__(self):
        return len(self._object)

    def __getitem__(self, key):
        try:
            return self.__getattr__(key)
        except AttributeError:
            raise KeyError(key)


class ProxyDict(ObjectWrapper):
    r"""
    Wraps a Vue proxy with a Python dict interface.
    """

    def __init__(self, proxy):
        from ipymuvue.pyodide.types import is_vue_proxy

        if not is_vue_proxy(proxy):
            raise TypeError("proxy must be a Vue proxy")

        super().__init__(proxy)

    def _vue_compatible(self, object):
        from ipymuvue.pyodide.proxies import vue_compatible

        return vue_compatible(object, reference=False)
