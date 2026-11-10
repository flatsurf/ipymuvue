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

import pytest

from ipymuvue.special import is_special


@pytest.mark.parametrize(
    "name", ["_private", "$el", "data", "setup", "mounted", "beforeUnmount"]
)
def test_special(name):
    assert is_special(name)


@pytest.mark.parametrize("name", ["count", "increment", "dataset"])
def test_not_special(name):
    assert not is_special(name)
