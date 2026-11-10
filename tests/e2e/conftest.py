r"""
Fixtures for end-to-end tests that render widgets in JupyterLab.

A JupyterLab server is started once per test session and each test drives it
with a headless browser through playwright.
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

import json
import os
import pathlib
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
import uuid

import pytest
from playwright.sync_api import expect

# Rendering widgets, in particular when they load pyodide, can take a while.
expect.set_options(timeout=30_000)

# User settings for JupyterLab that make the tests more reliable.
SETTINGS = {
    # Render all cells so they can be found in the DOM.
    "@jupyterlab/notebook-extension/tracker": {"windowingMode": "none"},
    # Do not show popups about news and updates.
    "@jupyterlab/apputils-extension/notification": {
        "fetchNews": "false",
        "checkForUpdates": False,
    },
}


class JupyterLab:
    r"""
    A running JupyterLab server serving notebooks from ``root``.
    """

    def __init__(self, root, port, token, process):
        self.root = root
        self.url = f"http://localhost:{port}"
        self.token = token
        self.process = process

    def api(self, method, path, body=None):
        request = urllib.request.Request(
            f"{self.url}/api/{path}",
            method=method,
            data=None if body is None else json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"token {self.token}"},
        )
        # Do not send requests to localhost through a proxy.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=10) as response:
            return json.loads(response.read() or "null")


def _free_port():
    with socket.socket() as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def jupyter_lab(tmp_path_factory):
    r"""
    Run JupyterLab with an isolated configuration for the duration of the
    test session.
    """
    root = tmp_path_factory.mktemp("notebooks")
    home = tmp_path_factory.mktemp("jupyter")

    settings = home / "settings"
    for plugin, values in SETTINGS.items():
        path = settings / f"{plugin}.jupyterlab-settings"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(values))

    env = dict(os.environ)
    env.update(
        JUPYTER_CONFIG_DIR=str(home / "config"),
        JUPYTER_RUNTIME_DIR=str(home / "runtime"),
        JUPYTERLAB_SETTINGS_DIR=str(settings),
        JUPYTERLAB_WORKSPACES_DIR=str(home / "workspaces"),
    )

    port = _free_port()
    token = secrets.token_hex(16)

    log = open(home / "jupyterlab.log", "w")
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "jupyterlab",
            "--no-browser",
            f"--port={port}",
            "--ServerApp.port_retries=0",
            f"--IdentityProvider.token={token}",
            f"--ServerApp.root_dir={root}",
            # Make window.jupyterapp available so we can drive JupyterLab.
            "--LabApp.expose_app_in_browser=True",
            # Use the frontend built in this repository (and not the copy
            # that was installed into the environment with ipymuvue.)
            f"--LabApp.extra_labextensions_path={pathlib.Path(__file__).parents[2] / 'ipymuvue' / 'labextensions'}",
        ],
        cwd=root,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )

    lab = JupyterLab(root, port, token, process)

    try:
        deadline = time.monotonic() + 60
        while True:
            if process.poll() is not None:
                raise RuntimeError(
                    f"JupyterLab exited:\n{(home / 'jupyterlab.log').read_text()}"
                )
            try:
                lab.api("GET", "status")
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.25)

        yield lab
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        log.close()


class CellError(Exception):
    r"""
    Raised when executing a cell in a notebook produced an error.
    """


class Notebook:
    r"""
    A notebook opened in JupyterLab with a running kernel.

    The notebook is created with the given ``cells``, a list of cells in the
    nbformat 4 format, and runs on the ``kernel`` with that name.
    """

    def __init__(self, page, lab, name, cells=(), kernel="python3"):
        self.page = page
        self.lab = lab
        self.name = name

        # Collect messages from the browser console so we can report them
        # when something goes wrong.
        self.console = []
        page.on(
            "console",
            lambda message: self.console.append(f"{message.type}: {message.text}"),
        )
        page.on("pageerror", lambda error: self.console.append(f"pageerror: {error}"))

        lab.api(
            "PUT",
            f"contents/{name}",
            {
                "type": "notebook",
                "format": "json",
                "content": {
                    "cells": list(cells),
                    "metadata": {
                        "kernelspec": {
                            "name": kernel,
                            "display_name": kernel,
                        }
                    },
                    "nbformat": 4,
                    "nbformat_minor": 5,
                },
            },
        )

        # Open the notebook, do not restore notebooks of previous tests.
        page.goto(f"{lab.url}/lab/tree/{name}?reset&token={lab.token}")

        # Wait for the notebook to open and its kernel to be ready.
        page.wait_for_function(
            r"""(name) => {
                const widget = window.jupyterapp?.shell.currentWidget;
                return widget?.context?.path === name && widget.sessionContext?.session?.kernel != null;
            }""",
            arg=name,
            timeout=60_000,
        )
        id = page.evaluate(
            r"""async () => {
                const widget = window.jupyterapp.shell.currentWidget;
                await widget.sessionContext.ready;
                await widget.sessionContext.session.kernel.info;
                return widget.id;
            }"""
        )

        self.panel = page.locator(f"[id='{id}']")

    def run(self, code):
        r"""
        Append a code cell with ``code`` to the notebook, execute it, and
        return a locator for the output area of the cell.

        Raises a :class:`CellError` if the cell produced an error.
        """
        index = self.page.evaluate(
            r"""(code) => {
                const notebook = window.jupyterapp.shell.currentWidget.content;
                const index = notebook.model.cells.length;
                notebook.model.sharedModel.insertCell(index, { cell_type: "code", source: code });
                return index;
            }""",
            code,
        )

        return self.execute(index)

    def execute(self, index):
        r"""
        Execute the cell at ``index`` and return a locator for its output
        area.

        Raises a :class:`CellError` if the cell produced an error.
        """
        error = self.page.evaluate(
            r"""async (index) => {
                const app = window.jupyterapp;
                const notebook = app.shell.currentWidget.content;

                notebook.activeCellIndex = index;
                await app.commands.execute("notebook:run-cell");

                const outputs = notebook.model.cells.get(index).toJSON().outputs ?? [];
                const error = outputs.find((output) => output.output_type === "error");
                return error ? `${error.ename}: ${error.evalue}\n${error.traceback.join("\n")}` : null;
            }""",
            index,
        )

        if error is not None:
            raise CellError(error)

        return (
            self.panel.locator(".jp-Notebook .jp-Cell")
            .nth(index)
            .locator(".jp-Cell-outputArea")
        )

    def execute_all(self):
        r"""
        Execute all cells of this notebook one after the other.

        Raises a :class:`CellError` if any cell produced an error.
        """
        count = self.page.evaluate(
            "() => window.jupyterapp.shell.currentWidget.content.model.cells.length"
        )
        for index in range(count):
            self.execute(index)

    @property
    def errors(self):
        r"""
        Return the errors that showed up in the browser console, i.e., uncaught
        exceptions and warnings from Vue.
        """
        return [
            message
            for message in self.console
            if message.startswith("pageerror:") or "[Vue warn]" in message
        ]

    def close(self):
        r"""
        Shut down the kernel of this notebook.
        """
        self.page.evaluate(
            r"""async () => {
                await window.jupyterapp.shell.currentWidget.sessionContext.shutdown();
            }"""
        )

    def __repr__(self):
        return f"Notebook({self.name!r})"


@pytest.fixture
def notebook(page, jupyter_lab, request):
    r"""
    A new notebook with a running Python kernel.
    """
    notebook = Notebook(
        page, jupyter_lab, f"{request.node.name}-{uuid.uuid4().hex[:8]}.ipynb"
    )

    yield notebook

    report(notebook, request)


def report(notebook, request):
    r"""
    Close ``notebook`` at the end of a test and make sure that there were no
    errors in the browser.
    """
    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else True:
        print("Browser console:", *notebook.console, sep="\n")

    notebook.close()

    assert not notebook.errors, "errors in the browser console:\n" + "\n".join(
        notebook.errors
    )


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    # Make the outcome of a test available to fixtures, see
    # https://docs.pytest.org/en/stable/example/simple.html#making-test-result-information-available-in-fixtures
    report = yield
    setattr(item, f"rep_{report.when}", report)
    return report
