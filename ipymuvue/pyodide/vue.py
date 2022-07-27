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
used to call into Vue directly through its JavaScript API. Note that calling
into Vue with any Python objects that are not primitives such as int or bool is
likely not going to work reliably.

Vue gets confused if it's presented any PyProxy objects, i.e., proxy objects
that live in JavaScript and wrap a Python object. There is no single reason why
exactly this is a problem but often, Vue tries to install its proxy
infrastructure which does not seem to play well the WASM objects that back the
pyodide implementation. To avoid such problems, the general strategy here is to
make sure that Vue only sees plain old JavaScript objects or sometimes things
that it will mostly leave alone such as shallow refs holding a PyProxy.

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

from ipymuvue_utils import Vue, withArity, getValue
from collections.abc import MutableMapping, MutableSequence


def define_component(*, setup=None, template=None, components=None, name=None, props=None, emits=None):
    r"""
    Return a new Vue component.

    A Vue component is a dict (more precisely a JavaScript object) as
    documented in the Vue API https://vuejs.org/api

    Currently, we only support the composition API, i.e., defining a setup()
    function instead of defining computed(), methods(), ...
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
        component.props = to_vue(props)

    if emits is not None:
        if not isinstance(emits, list) or not all(isinstance(prop, str) for prop in emits):
            raise TypeError("emits must be a list of strings")
        component.emits = to_vue(emits)

    if name is not None:
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        component.name = name

    return component


def prepare_setup(setup):
    def prepared_setup(props, context):
        python_props = create_pyproxy(props)

        exports = setup(python_props, context)

        if not isinstance(exports, dict):
            raise TypeError("setup must return a dict, e.g., locals()")

        import js
        js_exports = js.Object.new()
        for name in exports:
            if name.startswith("_"):
                # Should we warn? See #3.
                continue

            if exports[name] is python_props:
                continue

            setattr(js_exports, name, to_vue(exports[name]))

        return js_exports

    import pyodide
    return withArity(pyodide.ffi.create_proxy(prepared_setup), 2)


def prepare_components(components):
    for (name, component) in components.items():
        if not isinstance(name, str):
            raise TypeError("name of component must be a string")

        if hasattr(component, 'read'):
            # Component is a (.vue/.py) file. Load it with our VueComponentCompiler.
            from pathlib import Path
            key = None
            if hasattr(component, "name") and Path(component.name).suffix.lower() == ".py":
                key = "component"

            import pyodide

            @pyodide.create_proxy
            def read_file(fname):
                content = open(fname, 'rb').read()
                import js
                buffer = js.ArrayBuffer.new(len(content))
                buffer.assign(content)
                view = js.Uint8Array.new(buffer)
                return view

            from ipymuvue_vue_component_compiler import VueComponentCompiler

            component = VueComponentCompiler.new(read_file).compile(component.name)

            if key:
                component = getattr(component, key)

            # Cannot destroy because the component is async. See #9.
            # read_file.destroy()

        components[name] = component

    import pyodide
    import js
    return pyodide.ffi.to_js(components, dict_converter=js.Object.fromEntries)


class ProxyDict(MutableMapping):
    def __init__(self, proxy):
        self._proxy = proxy

    def __delitem__(self, key):
        raise Exception("not implemented __delitem__")

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __setitem__(self, key, value):
        if not isinstance(key, (int, str)):
            raise TypeError(f"key must be int or str but was {type(key)}")

        key = str(key)
        setattr(self._proxy, key, to_vue(value))

    def __iter__(self):
        import js
        for key in js.Object.keys(self._proxy):
            yield key

    def __len__(self):
        return len(self._proxy)

    def __getitem__(self, key):
        if not isinstance(key, (int, str)):
            raise TypeError(f"key must be int or str but was {type(key)}")

        key = str(key)
        value = getattr(self._proxy, key)
        return create_pyproxy(value)


class ProxyList(MutableSequence):
    def __init__(self, proxy):
        self._proxy = proxy

    def insert(self, index, object):
        raise NotImplementedError

    def __getitem__(self, index):
        return create_pyproxy(self._proxy[index])

    def __setitem__(self, index, value):
        raise NotImplementedError

    def __delitem__(self, index):
        raise NotImplementedError

    def __len__(self):
        return self._proxy.length


class ProxyRef:
    def __init__(self, ref):
        if not Vue.isRef(ref):
            raise TypeError
        self._ref = ref

    @property
    def value(self):
        return create_pyproxy(getValue(self._ref))

    @value.setter
    def value(self, value):
        self._ref.value = to_vue(value)


def create_pyproxy(x):
    if type(x) in [int, str, float, bool, type(None)]:
        return x

    if callable(x):
        return x

    if Vue.isRef(x):
        return ProxyRef(x)

    if Vue.isProxy(x):
        import js
        if js.Array.isArray(x):
            return ProxyList(x)

        if x.typeof != "object":
            raise Exception(f"not implemented, wrapping a proxy {x.typeof}")

        return ProxyDict(x)

    import js
    if js.Array.isArray(x):
        # TODO: Go deep?
        return list(x)

    # TODO: Go deep?
    return dict(js.Object.entries(x))


def to_vue(x, clone=False):
    if callable(x):
        return x

    if type(x) in [int, str, float, bool, type(None)]:
        import pyodide
        return pyodide.to_js(x)

    import pyodide
    if isinstance(x, pyodide.JsProxy):
        return x

    if isinstance(x, ProxyRef):
        assert Vue.isRef(x._ref)
        return x._ref

    if isinstance(x, ProxyDict) and not clone:
        return x._proxy

    if isinstance(x, ProxyList) and not clone:
        return x._proxy

    if isinstance(x, (MutableSequence, tuple)):
        import js
        y = js.Array.new()
        for item in x:
            y.push(to_vue(item))
        return y

    if isinstance(x, MutableMapping):
        import js
        o = js.Object.new()
        for key in x.keys():
            if not isinstance(key, (str, int)):
                raise TypeError(f"key must be str or int but was {type(key)}")
            strkey = str(key)
            if hasattr(o, strkey):
                raise ValueError("duplicate key in dict after conversion to str")
            setattr(o, strkey, to_vue(x[key]))

        return o

    raise Exception(f"not implemented for {type(x)}")


def ref(x):
    return create_pyproxy(Vue.ref(to_vue(x, clone=True)))


def watch(x, f):
    if not callable(x):
        raise TypeError("first argument to watch must be callable")

    # TODO: Enforce harder that no Python objects go into the Vue machinery.
    # Otherwise, they are turned into proxies and strange things tend to
    # happen. E.g., when omitting the to_vue here.
    def y():
        return to_vue(x())

    def on_change(current, previous, _):
        f(create_pyproxy(current), create_pyproxy(previous), _)

    import pyodide
    Vue.watch(pyodide.create_proxy(y), pyodide.create_proxy(on_change))


def computed(f):
    def g():
        return to_vue(f())

    from pyodide import create_proxy
    return create_pyproxy(Vue.computed(create_proxy(g)))
