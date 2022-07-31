r"""
Generic conversion between JavaScript and Python.

pyodide wraps JavaScript objects in a PyProxy and Python objects in a
JSProxy when the cross the boundary between JavaScript and Python and
vice versa.

However, this proxying causes trouble, see
:module:`ipymuvue.pyodide.vue`. In short, Python programmers expect a
Python dict interface and Vue gets confused by installing its own
proxy on top of the JsProxy.

Here, we provide some cenversions that seem to work better to enable
communication between Python and Vue.js JavaScript API.
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

from ipymuvue.pyodide.types import is_vue_ref, is_vue_proxy


def python_compatible(x):
    r"""
    Wrap ``x`` that came out of a Vue API for use in Python.
    """
    import pyodide
    import js

    from ipymuvue.pyodide.proxies.object_wrapper import ObjectWrapper, ProxyDict
    from ipymuvue.pyodide.proxies.array_wrapper import ArrayWrapper, ProxyList
    from ipymuvue.pyodide.proxies.proxy_ref import ProxyRef

    # Some elementary types are converted automatically by pyodide.
    if type(x) in [int, str, float, bool, type(None)]:
        return x

    if callable(x):
        assert isinstance(x, pyodide.ffi.JsProxy), "received a function from Vue that is not defined in JavaScript"
        raise NotImplementedError("cannot properly wrap functions from the Vue API yet")

    if is_vue_ref(x):
        return ProxyRef(x)

    if js.Array.isArray(x):
        if is_vue_proxy(x):
            return ProxyList(x)
        return ArrayWrapper(x)

    if x.typeof == "object":
        if is_vue_proxy(x):
            return ProxyDict(x)
        return ObjectWrapper(x)

    raise Exception(f"not implemented, wrapping a proxy {x.typeof}")


def vue_compatible(x, reference=True, shallow=False):
    r"""
    Return ``x`` as a native JavaScript object that can be safely consumed by
    the Vue API.

    If ``x`` is a primitive value such as a number or a string, return it
    unchanged.

    If ``reference`` is ``True``, returns a value that behaves like a reference
    of ``x``. Changes to ``x`` are reflected in the returned
    value and vice versa. If ``shallow`` is not set, verify that values nested
    in ``x`` are also compatible with Vue's JavaScript API. (That last part is
    sometimes not actually verified yet.)

    If ``reference`` is ``False``, return clone of ``x``; the clone is deep
    unless ``shallow`` is set.

    If ``reference`` is ``None``, return whatever is chepest to accomplish.
    """
    import js
    import pyodide

    from ipymuvue.pyodide.proxies.object_wrapper import ObjectWrapper
    from ipymuvue.pyodide.proxies.array_wrapper import ArrayWrapper
    from ipymuvue.pyodide.proxies.proxy_ref import ProxyRef

    if type(x) in [int, str, float, bool, type(None)]:
        return x

    if callable(x):
        if isinstance(x, pyodide.ffi.JsProxy):
            return x

        import asyncio
        if asyncio.iscoroutine(x):
            raise NotImplementedError("coroutines cannot be export by setup() yet, see ")

        # Load helper implemented in TypeScript in ipymuvue_js.ts
        from ipymuvue_js import asVueCompatibleFunction
        return asVueCompatibleFunction(pyodide.ffi.create_proxy(x), pyodide.ffi.create_proxy(python_compatible), pyodide.ffi.create_proxy(vue_compatible))

    if isinstance(x, pyodide.ffi.JsProxy):
        if reference is not False:
            # Note that we are not yet checking whether the insides of this
            # object contain no PyProxy instances.
            return x
        else:
            # Load helper implemented in TypeScript in ipymuvue_js.ts
            from ipymuvue_js import clone, cloneDeep
            return clone(x) if shallow else cloneDeep(x)

    if isinstance(x, ProxyRef):
        assert is_vue_ref(x._ref)
        return vue_compatible(x._ref, reference=reference, shallow=shallow)

    if isinstance(x, ObjectWrapper):
        return vue_compatible(x._object, reference=reference, shallow=shallow)

    if isinstance(x, ArrayWrapper):
        return vue_compatible(x._array, reference=reference, shallow=shallow)

    from collections.abc import Sequence
    if isinstance(x, Sequence):
        if reference is True:
            raise TypeError("cannot call Vue API with this Python sequence; use vue_compatible(..., reference=False) to create a deep clone that can be consumed by thue Vue API")
        else:
            y = js.Array.new()
            for item in x:
                y.push(vue_compatible(item, reference=None, shallow=shallow))
            return y

    from collections.abc import Mapping
    if isinstance(x, Mapping):
        if reference is True:
            raise TypeError("cannot call Vue API with this Python mapping; use vue_compatible(..., reference=False) to create a deep clone that can be consumed by the Vue API")
        else:
            o = js.Object.new()
            for key in x.keys():
                if not isinstance(key, (str, int)):
                    raise TypeError(f"key must be str or int but was {type(key)}")
                strkey = str(key)
                if hasattr(o, strkey):
                    raise ValueError("duplicate key in dict after conversion to str")
                setattr(o, strkey, vue_compatible(x[key], reference=None, shallow=shallow))

            return o

    raise NotImplementedError(f"cannot wrap this {type(x)} yet")
