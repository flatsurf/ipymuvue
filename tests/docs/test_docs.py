r"""
Check that the widgets embedded in the documentation render in a browser.

Build the documentation first, then run these tests, i.e., run
`pixi run test-docs`.
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

import functools
import http.server
import pathlib
import threading

import pytest
from playwright.sync_api import expect

HTML = pathlib.Path(__file__).parent.parent.parent / "docs" / "_build" / "html"

# Rendering widgets, in particular when they load pyodide, can take a while.
expect.set_options(timeout=60_000)


@pytest.fixture(scope="session")
def docs():
    r"""
    Serve the built documentation and return its URL.
    """
    if not (HTML / "index.html").exists():
        raise FileNotFoundError(f"{HTML} not found, build the documentation first")

    server = http.server.ThreadingHTTPServer(
        ("localhost", 0),
        functools.partial(http.server.SimpleHTTPRequestHandler, directory=HTML),
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://localhost:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture
def open_page(page, docs):
    r"""
    Return a function that opens a page of the documentation and make sure
    that there were no errors in the browser console.
    """
    console = []
    page.on(
        "console", lambda message: console.append(f"{message.type}: {message.text}")
    )
    page.on("pageerror", lambda error: console.append(f"pageerror: {error}"))

    def open(name):
        page.goto(f"{docs}/{name}")
        return page

    yield open

    errors = [
        message
        for message in console
        if message.startswith("pageerror:")
        or message.startswith("error:")
        or "[Vue warn]" in message
        or "Traceback (most recent call last)" in message
    ]
    assert not errors, "errors in the browser console:\n" + "\n".join(errors)


def test_tutorial(open_page):
    page = open_page("examples/Tutorial.html")

    # The last step of the tutorial renders a heading with a component
    # written in JavaScript and with one written in Python.
    expect(page.get_by_role("heading", name="Congratulations!")).to_have_count(2)

    # Step 10 fetches data from the web in the JavaScript and in the Python
    # component.
    expect(page.locator("pre", has_text="delectus aut autem")).to_have_count(2)


def test_demo(open_page):
    page = open_page("examples/Demo.html")

    # We match exactly since the source code of the notebook contains these
    # strings as well.
    expect(page.get_by_text("Hello Jupyter!", exact=True)).to_be_visible()
    expect(
        page.get_by_text("Component from an Asset String", exact=True)
    ).to_be_visible()


def test_graph_editor(open_page):
    page = open_page("examples/GraphEditor.html")

    # The static example graph has 3 vertices and each of the 3 editors
    # renders the 60 vertices of a BuckyBall.
    expect(page.locator("svg circle[fill='cornflowerblue']")).to_have_count(3 + 3 * 60)
