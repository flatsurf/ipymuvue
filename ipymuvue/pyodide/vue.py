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

import pyodide
from ipymuvue.pyodide.types import (
    String,
    Number,
    Boolean,
    Array,
    Object,
    Date,
    Function,
    Symbol,
)
from ipymuvue.pyodide.types import is_vue_ref, is_vue_proxy
from ipymuvue.pyodide.proxies import vue_compatible, python_compatible

# Load Vue from ipymuvue_js.ts implemented in TypeScript
from ipymuvue_js import Vue


def define_component(
    *, setup=None, template=None, components=None, name=None, props=None, emits=None
):
    r"""
    Return a new Vue component.

    A Vue component is a dict (more precisely a JavaScript object) as
    documented in the Vue API https://vuejs.org/api

    Currently, we only support the composition API, i.e., defining a setup()
    function instead of defining computed(), methods(), ...

    Digressing from the official API, the values of `components` can be open
    files. The component is then loaded from the file at runtime.
    """
    import js

    component = js.Object.new()

    from ipymuvue.pyodide.proxies import owner

    with owner(component):
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
            component.props = vue_compatible(props, reference=False)

        if emits is not None:
            if not isinstance(emits, list) or not all(
                isinstance(prop, str) for prop in emits
            ):
                raise TypeError("emits must be a list of strings")

            component.emits = vue_compatible(emits, reference=False)

        if name is not None:
            if not isinstance(name, str):
                raise TypeError("name must be a string")
            component.name = name

    return component


def prepare_setup(setup):
    r"""
    Wraps a setup function to make it compatible with the Vue API.
    """

    from ipymuvue.pyodide.proxies import create_proxy

    @create_proxy
    def prepared_setup(props, context):
        import js

        js_exports = js.Object.new()

        from ipymuvue.pyodide.proxies import owner

        with owner(js_exports):
            assert is_vue_proxy(props)

            # The props are a Vue proxy. Wrap it so that it behaves like a Python
            # object, e.g., so its entries appear to be dicts and lists.
            props = python_compatible(props)

            exports = setup(props, context)

            if not isinstance(exports, dict):
                raise TypeError("setup() must return a dict, e.g., locals()")

            for name in exports:
                from ipymuvue.special import is_special

                if is_special(name):
                    # Should we write a warning to the console? See #6.
                    continue

                try:
                    export = vue_compatible(exports[name])
                except Exception:
                    raise TypeError(
                        f"could not convert {name} returned by setup() to be used in the component template"
                    )

                setattr(js_exports, name, export)

        return js_exports

    # Vue checks the arity of the setup function to decide whether to call with
    # a `context` parameter or use an optimized call without `context`.
    # The arity of Python functions is always zero from JavaScript's
    # perspective so we need to fix the arity to get a context.

    # Load helper implemented in TypeScript in ipymuvue_js.ts
    from ipymuvue_js import withArity

    return withArity(prepared_setup, 2)


def prepare_components(components):
    r"""
    Rewrite the subcomponents dict to make it compatible with the Vue API.
    """

    for (name, component) in components.items():
        if not isinstance(name, str):
            raise TypeError("name of component must be a string")

        # If the component is a (.vue/.py) file. Load it with our VueComponentCompiler.
        if hasattr(component, "read"):
            from pathlib import Path

            fname = component.name if hasattr(component, "name") else None

            from ipymuvue.pyodide.proxies import create_proxy

            @create_proxy
            def read_file_from_wasm(fname):
                content = open(fname, "rb").read()

                import js

                buffer = js.ArrayBuffer.new(len(content))

                buffer.assign(content)
                view = js.Uint8Array.new(buffer)
                return view

            if fname is None:
                raise NotImplementedError(
                    "cannot compile components from string in the frontend yet"
                )

            from ipymuvue_vue_component_compiler import VueComponentCompiler

            component = VueComponentCompiler.new(read_file_from_wasm).compile(fname)

            # Since Python files have no default export, we use the global
            # variable "component" instead.
            if Path(fname).suffix.lower() == ".py":
                component = getattr(component, "component")

            # Cannot destroy because the component is async. See #9.
            # read_file.destroy()

        if (
            not isinstance(component, pyodide.ffi.JsProxy)
            or component.typeof != "object"
        ):
            raise TypeError("component must be a JavaScript object")

        components[name] = component

    return vue_compatible(components, reference=None, shallow=True)


def reactive(value):
    r"""
    Create a reactive proxy of ``value``.
    """
    if is_vue_ref(value) or is_vue_proxy(value):
        pass
    else:
        value = vue_compatible(value, reference=True)

    return python_compatible(Vue.reactive(value))


def ref(value):
    r"""
    Create a Vue Ref with initial ``value``.
    """
    if is_vue_ref(value) or is_vue_proxy(value):
        pass
    else:
        value = vue_compatible(value, reference=False)

    return python_compatible(Vue.ref(value))


def watch(watched, on_change):
    r"""
    Watch the result of ``watched`` which must be or produce a Vue Ref or a Vue
    Proxy.

    Note the difference between watching ``a.b`` and watching ``lambda: a.b``.
    The former watches ``b`` for changes, but won't notice when be gets
    replaced completely as in ``a.b = None``. The later also captures such
    changes (and is usually what you want.)

    When it changes, run ``on_change``.
    """
    if callable(watched):

        from ipymuvue.pyodide.proxies import create_proxy

        @create_proxy
        def _watched():
            reactive = vue_compatible(watched(), shallow=True)
            if not is_vue_ref(reactive) and not is_vue_proxy(reactive):
                raise TypeError(
                    "watched object must be Vue Ref or a reactive Vue Proxy"
                )
            return reactive

    else:
        watched = vue_compatible(watched, shallow=True)
        if not is_vue_ref(watched) and not is_vue_proxy(watched):
            raise TypeError("watched object must be Vue Ref or a reactive Vue Proxy")
        _watched = watched

    from ipymuvue.pyodide.proxies import create_proxy

    @create_proxy
    def _on_change(current, previous, on_cleanup):
        on_change(python_compatible(current), python_compatible(previous), on_cleanup)

    return Vue.watch(_watched, _on_change)


def computed(getter):
    r"""
    Return a readonly Vue Ref that contains the value produced by ``getter``.

    The value produce by ``getter`` must be compatible with
    ``as_vue_compatible`` since Vue is going to install its reactivity hooks
    into it. If returning a list or a dict, use ``to_vue_compatible``
    explicitly inside the getter to make the value compatible.
    """

    from ipymuvue.pyodide.proxies import create_proxy

    @create_proxy
    def _getter():
        return vue_compatible(getter(), reference=None)

    return python_compatible(Vue.computed(_getter))


def on_mounted(callback):
    r"""
    Register ``callback`` to be called after the component has been mounted.
    """
    Vue.onMounted(vue_compatible(callback))


def on_updated(callback):
    r"""
    Register ``callback`` to be called after the component has updated its DOM
    tree due to a reactive state change.
    """
    Vue.onUpdated(vue_compatible(callback))


def on_unmounted(callback):
    r"""
    Register ``callback`` to be called atfer the component has been unmounted.
    """
    Vue.onUnmounted(vue_compatible(callback))


def on_before_mount(callback):
    r"""
    Register ``callback`` to be called right before the component is to be mounted.
    """
    Vue.noBeforeMount(vue_compatible(callback))


def on_before_update(callback):
    r"""
    Register ``callback`` to be called right before the component is about to update.
    """
    Vue.onBeforeUpdate(vue_compatible(callback))


def on_before_unmount(callback):
    r"""
    Register ``callback`` to be called right before a component instance is to
    be unmounted.
    """
    Vue.onBeforeUnmount(vue_compatible(callback))


def on_activated(callback):
    r"""
    Register ``callback`` to be called after the component instance is inserted
    into the DOM as part of a tree cache by ``<KeepAlive>``.
    """
    Vue.onActivated(vue_compatible(callback))


def on_deactivated(callback):
    r"""
    Register ``callback`` to be called after the component instance is removed
    from the DOM as part of a tree cached by ``<KeepAlive>``.
    """
    Vue.onDeactivated(vue_compatible(callback))


__all__ = [
    "define_component",
    "ref",
    "reactive",
    "watch",
    "computed",
    "on_mounted",
    "on_updated",
    "on_unmounted",
    "on_before_mount",
    "on_before_update",
    "on_before_unmount",
    "on_activated",
    "on_deactivated",
    "String",
    "Number",
    "Boolean",
    "Array",
    "Object",
    "Date",
    "Function",
    "Symbol",
]
