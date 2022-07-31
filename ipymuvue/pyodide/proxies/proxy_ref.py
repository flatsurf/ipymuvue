r"""
Wrapper for a Vue.js Ref.

We provide a Vue.js Ref with a more convenient interface from Python
and make sure that no Python objects that Vue.js cannot understand
enter the Vue.js API.
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


class ProxyRef:
    r"""
    Wraps a Vue ref object with a Python property interface.
    """

    def __init__(self, ref):
        from ipymuvue.pyodide.types import is_vue_ref

        if not is_vue_ref(ref):
            raise TypeError("ref must be a Vue ref")
        self._ref = ref

    @property
    def value(self):
        # For a readonly ref, Python does not see its .value attribute so we
        # run the .value in JavaScript.
        from ipymuvue.pyodide.proxies import python_compatible

        # Load Vue from ipymuvue_js.ts implemented in TypeScript
        from ipymuvue_js import Vue

        return python_compatible(Vue.unref(self._ref))

    @value.setter
    def value(self, value):
        from ipymuvue.pyodide.proxies import vue_compatible

        self._ref.value = vue_compatible(value, reference=False)
