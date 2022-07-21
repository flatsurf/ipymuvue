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
    name = "__VUE_COMPONENT_COMPILER__"

    import sys
    if name not in sys.modules:
        import importlib
        sys.modules[name] = importlib.util.module_from_spec(importlib.util.spec_from_loader(name, loader=None))

    if value is not None:
        sys.modules[name].name = value

    return sys.modules[name].name


def define_component(template=None, components=None):
    r"""
    Return a new Vue component.

    A Vue component is a dict (more precisely a JavaScript object) as
    documented in the Vue API https://vuejs.org/api/#options-api
    """
    import js
    component = js.Object()

    if template is not None:
        component.template = template

    if components is not None:
        component.components = prepare_components(components)

    return component


def prepare_components(components):
    import pyodide
    import js

    for (name, component) in components.items():
        if hasattr(component, 'read'):
            # Component is a (.vue) file. Load it with our
            # VueComponentCompiler.
            # TODO: We shuold be more careful and in other places to get the paths right.
            components[name] = __VUE_COMPONENT_COMPILER__().compile(component.name)
            print(name, components[name])

    return pyodide.ffi.to_js(components, dict_converter=js.Object.fromEntries)


__all__ = ["define_component", "__VUE_COMPONENT_COMPILER__"]
