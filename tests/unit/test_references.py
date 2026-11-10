r"""
Tests for invoking methods of Vue components from Python.

These tests simulate the frontend by answering the messages that the widget
sends. See ``tests/e2e/`` for tests with an actual frontend.
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

import asyncio
import json

import pytest

from ipymuvue.widgets import VueWidget
from ipymuvue.widgets.references import InvocationError


class Frontend:
    r"""
    A fake frontend for ``widget`` that answers each invocation with the
    output of ``respond``.
    """

    def __init__(self, widget, respond):
        self.widget = widget
        self.respond = respond
        self.messages = []

        widget.send = self.send

    def send(self, content, buffers=None):
        # Messages are sent as JSON so, e.g., tuples become lists.
        content = json.loads(json.dumps(content))
        self.messages.append(content)

        results = self.respond(content)
        if results is None:
            return

        # Answer asynchronously, like a real frontend would.
        asyncio.get_running_loop().call_soon(
            self.widget._handle_custom_msg,
            {"identifier": content["identifier"], "results": results},
            [],
        )


@pytest.fixture
def widget():
    return VueWidget(template="<div ref='outer'><child ref='inner'/></div>")


async def test_invocation_message(widget):
    frontend = Frontend(widget, lambda content: [{"view": "v", "result": 1}])

    assert await widget["outer"]["inner"].method(1, "two", poll=False) == [1]

    (message,) = frontend.messages
    assert message["target"] == "method"
    assert message["path"] == ["outer", "inner"]
    assert message["args"] == [1, "two"]
    assert message["return_when"] == "FIRST_EXCEPTION"
    assert message["views"] is None


async def test_first_exception(widget):
    Frontend(widget, lambda content: [
        {"view": "v1", "result": 1},
        {"view": "v2", "result": 2},
    ])

    assert await widget["ref"].method(poll=False) == [1, 2]
    assert await widget["ref"].method(poll=False, identify=True) == [(1, "v1"), (2, "v2")]


async def test_first_exception_with_error(widget):
    Frontend(widget, lambda content: [
        {"view": "v1", "result": 1},
        {"view": "v2", "error": "boom"},
    ])

    with pytest.raises(InvocationError) as error:
        await widget["ref"].method(poll=False)

    assert error.value.identifier == "v2"


async def test_first_completed(widget):
    Frontend(widget, lambda content: [{"view": "v1", "result": 1}])

    assert await widget["ref"].method(poll=False, return_when="FIRST_COMPLETED") == 1
    assert await widget["ref"].method(poll=False, return_when="FIRST_COMPLETED", identify=True) == [1, "v1"]


async def test_single_view(widget):
    frontend = Frontend(widget, lambda content: [{"view": "v1", "result": 1}])

    assert await widget["ref"].method(poll=False, views="v1") == 1
    assert frontend.messages[0]["views"] == "v1"


async def test_single_view_with_error(widget):
    Frontend(widget, lambda content: [{"view": "v1", "error": "boom"}])

    with pytest.raises(InvocationError):
        await widget["ref"].method(poll=False, views="v1")


async def test_all_completed(widget):
    Frontend(widget, lambda content: [
        {"view": "v1", "result": 1},
        {"view": "v2", "error": "boom"},
    ])

    first, second = await widget["ref"].method(poll=False, return_when="ALL_COMPLETED")

    assert await first == 1
    with pytest.raises(InvocationError):
        await second


async def test_single_view_not_mounted(widget):
    # The frontend reports no results if the ref is not mounted in that view.
    Frontend(widget, lambda content: [])

    with pytest.raises(ValueError, match="exactly one result"):
        await widget["ref"].method(poll=False, views="v1")


async def test_ignore(widget):
    frontend = Frontend(widget, lambda content: None)

    assert await widget["ref"].method(poll=False, return_when="IGNORE") is None
    assert frontend.messages[0]["return_when"] == "IGNORE"


async def test_unrelated_messages_are_ignored(widget):
    def respond(content):
        widget._handle_custom_msg({"identifier": "unrelated", "results": []}, [])
        return [{"view": "v", "result": 1}]

    Frontend(widget, respond)

    assert await widget["ref"].method(poll=False) == [1]
