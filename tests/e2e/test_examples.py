r"""
Run the example notebooks in examples/ in JupyterLab.
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

import pathlib
import shutil

import pytest
from playwright.sync_api import expect

from conftest import Notebook, report

EXAMPLES = pathlib.Path(__file__).parent.parent.parent / "examples"


@pytest.fixture
def example(page, jupyter_lab, request):
    r"""
    Return a function that opens one of the notebooks in examples/ in
    JupyterLab.
    """
    notebooks = []

    def open(name):
        import jupytext

        examples = jupyter_lab.root / "examples"
        if not examples.exists():
            shutil.copytree(EXAMPLES, examples)

        notebook = jupytext.read(EXAMPLES / name)
        notebook.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}

        notebook = Notebook(page, jupyter_lab, f"examples/{pathlib.Path(name).stem}.ipynb", cells=notebook.cells)
        notebooks.append(notebook)
        return notebook

    yield open

    for notebook in notebooks:
        report(notebook, request)


def test_demo(example):
    notebook = example("Demo.md")
    notebook.execute_all()

    expect(notebook.panel.get_by_text("Hello Jupyter!")).to_be_visible()
    expect(notebook.panel.get_by_text("Component from an Asset String")).to_be_visible()
