r"""
Names of special functions in the Vue API.
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

options = [
    "data",
    "props",
    "computed",
    "methods",
    "watch",
    "emits",
    "expose",
    "template",
    "render",
    "provide",
    "inject",
    "setup",
    "name",
    "inheritAttrs",
    "components",
    "directives",
]

lifecycle = [
    "beforeCreate",
    "created",
    "beforeMount",
    "mounted",
    "beforeUpdate",
    "updated",
    "beforeUnmount",
    "unmounted",
    "errorCaptured",
    "renderTracked",
    "renderTriggered",
    "activated",
    "deactivated",
    "serverPrefetch",
]


def is_special(name):
    r"""
    Return whether `name` has a special meaning in a Vue component.
    """
    if name.startswith("_"):
        return True

    if name.startswith("$"):
        return True

    if name in options:
        return True

    if name in lifecycle:
        return True

    return False
