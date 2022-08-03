r"""
Asynchronous invocation of methods on Vue components.
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


async def run(future, poll=True):
    r"""
    Await ``future``.

    If ``poll`` is set, do so without blocking the Jupyter notebook.
    """
    future = asyncio.ensure_future(future)

    if poll:
        events = 1
        delay = 0.001

        import jupyter_ui_poll

        async with jupyter_ui_poll.ui_events() as poll:
            while not future.done():
                await poll(events)

                events = min(events + 1, 64)

                await asyncio.sleep(delay)

                # Wait for at most 250ms, the reaction time of most
                # people, https://stackoverflow.com/a/44755058/812379.
                delay = min(2 * delay, 0.25)

    assert future.done()
    return await future
