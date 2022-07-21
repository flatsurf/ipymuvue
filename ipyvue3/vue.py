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


def __VUE_COMPONENT_COMPILER__(value = None):
    r"""
    Return some VueComponentCompiler instance as defined in JavaScript.

    TODO: This is a hack. We keep a reference to the latest instance used whose
    assets might be completely wrong. Instead we should instantiate our own
    compiler and run with the latest assets from the virtual file system.
    """
    name = "__VUE_COMPONENT_COMPILER__"

    import sys
    if name not in sys.modules:
        import importlib
        sys.modules[name] = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None))

    if value is not None:
        sys.modules[name].name = value

    return sys.modules[name].name


def define_component(template=None, components=None, props=None, name=None):
    r"""
    Return a new Vue component.

    A Vue component is a dict (more precisely a JavaScript object) as
    documented in the Vue API https://vuejs.org/api/#options-api
    """
    import js
    component = js.Object.new()

    if template is not None:
        component.template = template

    if components is not None:
        component.components = prepare_components(components)

    if props is not None:
        component.props = prepare_props(props)

    if name is not None:
        component.name = name

    return component


def set_default_export(globals, object):
    # TODO: Explain, check type.
    globals.update({key: getattr(object, key) for key in dir(object)})


def prepare_components(components):
    for (name, component) in components.items():
        if not isinstance(name, str):
            raise TypeError("name of component must be a string")

        if hasattr(component, 'read'):
            # Component is a (.vue) file. Load it with our VueComponentCompiler.
            # TODO: We should be more careful and in other places to get the paths right.
            component = __VUE_COMPONENT_COMPILER__().compile(component.name)

        components[name] = component

    import pyodide
    import js
    return pyodide.ffi.to_js(components, dict_converter=js.Object.fromEntries)


def prepare_props(props):
    import js
    return js.Array(*props)


__all__ = ["define_component", "__VUE_COMPONENT_COMPILER__"]
