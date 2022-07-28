r"""
The Vue API in Python.

This module is automatically provided with the "assets" available when defining
vue components.

The general strategy of this module is to make sure that Vue.js never sees any
pyodide PyProxy objects and that the Python developer is not bothered with
JsProxy objects. The former is necessary for Vue to function, the latter is
mostly a convenience.

==============================
Accessing the Vue API directly
==============================

We export the `vue` module as `Vue`. If you know what you are doing, it can be
used to call into Vue directly using its JavaScript API. Note that calling
into Vue with any Python objects that are not primitives such as int or bool is
likely not going to work reliably.

Things tend to go wrong when Vue is presented any PyProxy objects, i.e., proxy
objects that live in JavaScript and wrap a Python object. The truth is that
it's not clear to us what exactly is the problem here but there seem to be
issues when Vue is installing its own proxy on the PyProxy. This changes the
identity of these objects, so pyodide is going to rewrap these proxies using a
JsProxy. Also, methods called on these objects are not going through the Vue
proxy machinery.

In the opposite direction, there is essenially the same problem. It's certainly
very inconvenient for Python developers to be able to call into Vue with Python
objects such as dicts and lists and at the same time receive JsProxy objects
that are Object and Array since the interface of the former is quite different
from a dict. The bigger problem here is however, if we return a reactive Object
to Python at some point, Python code might modify it and insert a PyProxy such
as a dict somewhere. We can't really do anything about such operations and Vue
is going to stop to function as outlined above. So our strategy here is to make
sure that the objects we return are proxy objects that emulate a Python
interface such as :class:`ProxyDict`, :class:`ProxyList` and at the same time
rewrite all modifications to be compatible with Vue's expectations. Sometimes,
we also return read-only objects or just convert things to dicts or lists if we
find that the connection to the Vue machinery is not needed and such conversion
is easier.
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

from ipymuvue_utils import Vue, withArity, cloneDeep, clone, asVueCompatibleFunction
from collections.abc import MutableMapping, MutableSequence


def define_component(*, setup=None, template=None, components=None, name=None, props=None, emits=None):
    r"""
    Return a new Vue component.

    A Vue component is a dict (more precisely a JavaScript object) as
    documented in the Vue API https://vuejs.org/api

    Currently, we only support the composition API, i.e., defining a setup()
    function instead of defining computed(), methods(), ...

    Digressing from the official API, the values of `components` can be
    filenames. The component is then loaded from the file at runtime.
    """
    import js
    component = js.Object.new()

    if setup is not None:
        if not callable(setup):
            raise TypeError("setup must be a function")
        component.setup = prepare_setup(setup)

    if template is not None:
        if not isinstance(template, str):
            raise TypeError("template must be a string")
        component.template = template

    if components is not None:
        if not isinstance(components, dict):
            raise TypeError("components must be a dict")
        component.components = prepare_components(components)

    if props is not None:
        if not isinstance(props, list) or not all(isinstance(prop, str) for prop in props):
            raise TypeError("props must be a list of strings")
        component.props = vue_compatible(props, reference=False)

    if emits is not None:
        if not isinstance(emits, list) or not all(isinstance(prop, str) for prop in emits):
            raise TypeError("emits must be a list of strings")
        component.emits = vue_compatible(emits, reference=False)

    if name is not None:
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        component.name = name

    return component


def _is_vue_proxy(x):
    r"""
    Return whether ``x`` is a un unwrapped reactive Vue Proxy.
    """
    import pyodide
    return isinstance(x, pyodide.ffi.JsProxy) and Vue.isProxy(x)


def _is_vue_ref(x):
    r"""
    Return whether ``x`` is a un unwrapped reactive Vue Ref.
    """
    import pyodide
    return isinstance(x, pyodide.ffi.JsProxy) and Vue.isRef(x)


def prepare_setup(setup):
    r"""
    Wraps a setup function to make it compatible with the Vue API.
    """
    import pyodide

    @pyodide.ffi.create_proxy
    def prepared_setup(props, context):
        # The props are a Vue proxy. Wrap it so that it behaves like a Python,
        # e.g., so its entries appear to be dicts and lists.
        assert _is_vue_proxy(props)
        props = create_pyproxy(props)

        exports = setup(props, context)

        if not isinstance(exports, dict):
            raise TypeError("setup() must return a dict, e.g., locals()")

        import js
        js_exports = js.Object.new()

        for name in exports:
            from ipymuvue.special import is_special
            if is_special(name):
                # Should we write a warning to the console? See #6.
                continue

            try:
                export = vue_compatible(exports[name])
            except Exception:
                raise TypeError(f"could not convert {name} returned by setup() to be used in the component template")

            setattr(js_exports, name, export)

        return js_exports

    # Vue checks the arity of the setup function to decide whether to call with
    # a `context` parameter or use an optimized call without `context`.
    # The arity of Python functions is always zero from JavaScript's
    # perspective so we need to fix the arity to get a context.
    return withArity(prepared_setup, 2)


def prepare_components(components):
    r"""
    Rewrite the subcomponents dict to make it compatible with the Vue API.
    """
    import pyodide

    for (name, component) in components.items():
        if not isinstance(name, str):
            raise TypeError("name of component must be a string")

        # If the component is a (.vue/.py) file. Load it with our VueComponentCompiler.
        if hasattr(component, 'read'):
            from pathlib import Path
            fname = component.name if hasattr(component, "name") else None
            component_name = Path(fname).stem or name

            @pyodide.ffi.create_proxy
            def read_file_from_wasm(fname):
                content = open(fname, 'rb').read()
                import js
                buffer = js.ArrayBuffer.new(len(content))
                buffer.assign(content)
                view = js.Uint8Array.new(buffer)
                return view

            from ipymuvue_vue_component_compiler import VueComponentCompiler

            if fname is None:
                raise NotImplementedError("cannot compile components from string in the frontend yet")

            component = VueComponentCompiler.new(read_file_from_wasm).compile(fname)

            # Since Python files have no default export, we use the global
            # variable "component" instead.
            if Path(fname).suffix.lower() == ".py":
                component = getattr(component, "component")

            # Cannot destroy because the component is async. See #9.
            # read_file.destroy()

        if not isinstance(component, pyodide.ffi.JsProxy) or component.typeof != "object":
            raise TypeError("component must be a JavaScript object")

        components[name] = component

    return vue_compatible(components, reference=None, shallow=True)


class ObjectWrapper(MutableMapping):
    r"""
    Wraps a JavaScript object with a Python dict interface.
    """

    def __init__(self, object):
        if not object.typeof == "object":
            raise TypeError("object must be a JavaScript object")

        self._object = object

    def __delitem__(self, key):
        raise Exception("not implemented __delitem__")

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __setitem__(self, key, value):
        if not isinstance(key, (int, str)):
            raise TypeError(f"key must be int or str but was {type(key)}")

        setattr(self._object, str(key), vue_compatible(value))

    def __iter__(self):
        import js
        for key in js.Object.keys(self._object):
            yield key

    def __len__(self):
        return len(self._object)

    def __getitem__(self, key):
        if not isinstance(key, (int, str)):
            raise TypeError(f"key must be int or str but was {type(key)}")

        return create_pyproxy(getattr(self._object, str(key)))


class ProxyDict(ObjectWrapper):
    r"""
    Wraps a Vue proxy with a Python dict interface.
    """

    def __init__(self, proxy):
        if not _is_vue_proxy(proxy):
            raise TypeError("proxy must be a Vue proxy")

        super().__init__(proxy)

    def __setitem__(self, key, value):
        if not isinstance(key, (int, str)):
            raise TypeError(f"key must be int or str but was {type(key)}")

        setattr(self._object, str(key), vue_compatible(value, reference=False))


class ArrayWrapper(MutableSequence):
    r"""
    Wraps a JavaScript Array with a Python list interface.
    """

    def __init__(self, array):
        import js
        if not js.Array.isArray(array):
            raise TypeError("array must be a JavaScript array")

        self._array = array

    def insert(self, index, object):
        raise NotImplementedError("writing to a list proxy is not implemented yet")

    def __getitem__(self, index):
        return create_pyproxy(self._array[index])

    def __setitem__(self, index, value):
        raise NotImplementedError("writing to a list proxy is not implemented yet")

    def __delitem__(self, index):
        raise NotImplementedError("writing to a list proxy is not implemented yet")

    def __len__(self):
        return self._array.length


class ProxyList(ArrayWrapper):
    r"""
    Wraps a Vue proxy with a Python list interface.
    """

    def __init__(self, proxy):
        if not _is_vue_proxy(proxy):
            raise TypeError("proxy must be a Vue proxy")
        super().__init__(proxy)


class ProxyRef:
    r"""
    Wraps a Vue ref object with a Python property interface.
    """

    def __init__(self, ref):
        if not _is_vue_ref(ref):
            raise TypeError("ref must be a Vue ref")
        self._ref = ref

    @property
    def value(self):
        # For a readonly ref, Python does not see its .value attribute so we
        # run the .value in JavaScript.
        return create_pyproxy(Vue.unref(self._ref))

    @value.setter
    def value(self, value):
        self._ref.value = vue_compatible(value, reference=False)


def create_pyproxy(x):
    r"""
    Wrap ``x`` that came out of a Vue API for use in Python.
    """
    # Some elementary types are converted automatically by pyodide.
    if type(x) in [int, str, float, bool, type(None)]:
        return x

    if callable(x):
        import pyodide
        assert isinstance(x, pyodide.ffi.JsProxy), "received a function from Vue that is not defined in JavaScript"
        raise NotImplementedError("cannot properly wrap functions from the Vue API yet")

    if _is_vue_ref(x):
        return ProxyRef(x)

    import js
    if js.Array.isArray(x):
        if _is_vue_proxy(x):
            return ProxyList(x)
        return ArrayWrapper(x)

    if x.typeof == "object":
        if _is_vue_proxy(x):
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
    import pyodide

    if type(x) in [int, str, float, bool, type(None)]:
        return x

    if callable(x):
        if isinstance(x, pyodide.ffi.JsProxy):
            return x

        return asVueCompatibleFunction(pyodide.ffi.create_proxy(x), pyodide.ffi.create_proxy(create_pyproxy), pyodide.ffi.create_proxy(vue_compatible))

    if isinstance(x, pyodide.ffi.JsProxy):
        if reference is not False:
            # Note that we are not yet checking whether the insides of this
            # object contain no PyProxy instances.
            return x
        else:
            return clone(x) if shallow else cloneDeep(x)

    if isinstance(x, ProxyRef):
        assert _is_vue_ref(x._ref)
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
            import js
            y = js.Array.new()
            for item in x:
                y.push(vue_compatible(item, reference=None, shallow=shallow))
            return y

    from collections.abc import Mapping
    if isinstance(x, Mapping):
        if reference is True:
            raise TypeError("cannot call Vue API with this Python mapping; use vue_compatible(..., reference=False) to create a deep clone that can be consumed by the Vue API")
        else:
            import js
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


def ref(value):
    r"""
    Create a Vue Ref with initial ``value``.
    """
    if _is_vue_ref(value) or _is_vue_proxy(value):
        pass
    else:
        value = vue_compatible(value, reference=False)

    return create_pyproxy(Vue.ref(value))


def watch(watched, on_change):
    r"""
    Watch the result of ``watched`` which must produce a Vue Ref or a Vue Proxy.

    When it changes, run ``on_change``.
    """
    if not callable(watched):
        raise TypeError("first argument to watch must be callable")

    import pyodide

    @pyodide.ffi.create_proxy
    def _watched():
        reactive = vue_compatible(watched(), shallow=True)
        if not _is_vue_ref(reactive) and not _is_vue_proxy(reactive):
            raise TypeError("watched object must be Vue Ref or a reactive Vue Proxy")
        return reactive

    @pyodide.ffi.create_proxy
    def _on_change(current, previous, on_cleanup):
        on_change(create_pyproxy(current), create_pyproxy(previous), on_cleanup)

    import pyodide
    return Vue.watch(_watched, _on_change)


def computed(getter):
    r"""
    Return a readonly Vue Ref that contains the value produced by ``getter``.

    The value produce by ``getter`` must be compatible with
    ``as_vue_compatible`` since Vue is going to install its reactivity hooks
    into it. If returning a list or a dict, use ``to_vue_compatible``
    explicitly inside the getter to make the value compatible.
    """
    import pyodide

    @pyodide.ffi.ceate_proxy
    def _getter():
        return vue_compatible(getter(), reference=None)

    return create_pyproxy(Vue.computed(_getter))
