r"""
Tests for the Python side of :class:`ipymuvue.widgets.VueWidget`.

These tests do not need a frontend. See ``tests/e2e/`` for tests that render
widgets in JupyterLab.
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

import io

import pytest
from traitlets import Unicode

from ipymuvue.widgets import VueWidget


class Hello(VueWidget):
    def __init__(self, **kwargs):
        super().__init__(template="<h1>Hello {{ audience }}!</h1>", **kwargs)

    audience = Unicode("World").tag(sync=True)

    @VueWidget.callback
    def exclaim(self, suffix="!"):
        self.audience += suffix

    def not_a_callback(self):
        pass


def test_template_and_type():
    widget = Hello()

    assert widget._VueWidget__template == "<h1>Hello {{ audience }}!</h1>"
    assert widget._VueWidget__type == "Hello"


def test_model_and_view():
    from ipymuvue import __version__

    widget = Hello()

    state = widget.get_state()
    assert state["_model_name"] == "VueWidgetModel"
    assert state["_view_name"] == "VueWidgetView"
    assert state["_model_module"] == "ipymuvue"
    assert state["_model_module_version"] == f"^{__version__}"
    assert state["audience"] == "World"


def test_callbacks_are_exposed():
    widget = Hello()

    assert widget._VueWidget__methods == ["exclaim"]


def test_callback_invoked_from_frontend():
    widget = Hello()

    widget._handle_message(widget, {"method": "exclaim", "args": []}, [])
    assert widget.audience == "World!"

    widget._handle_message(widget, {"method": "exclaim", "args": ["?"]}, [])
    assert widget.audience == "World!?"


def test_without_capture_output():
    widget = Hello(capture_output=False)

    widget._handle_message(widget, {"method": "exclaim", "args": []}, [])
    assert widget.audience == "World!"


def test_components_from_strings_become_assets():
    widget = VueWidget(
        template="<child/>",
        components={"child": "<template><div>child</div></template>"},
    )

    components = widget._VueWidget__components
    assets = widget._VueWidget__assets

    asset = components["child"]
    assert asset.endswith(".vue")
    assert assets[asset] == b"<template><div>child</div></template>"


def test_components_from_files_become_assets(tmp_path):
    vue = tmp_path / "Child.vue"
    vue.write_text("<template><div>child</div></template>")

    with open(vue) as f:
        widget = VueWidget(template="<child/>", components={"child": f})

    assert widget._VueWidget__components == {"child": "Child.vue"}
    assert (
        widget._VueWidget__assets["Child.vue"]
        == b"<template><div>child</div></template>"
    )


def test_components_from_assets():
    widget = VueWidget(
        template="<child/>",
        components={"child": "Child.vue"},
        assets={"Child.vue": io.BytesIO(b"<template><div>child</div></template>")},
    )

    assert widget._VueWidget__components == {"child": "Child.vue"}
    assert (
        widget._VueWidget__assets["Child.vue"]
        == b"<template><div>child</div></template>"
    )


def test_ipymuvue_is_shipped_as_asset():
    widget = VueWidget(template="<div/>")

    assets = widget._VueWidget__assets

    # The modules that implement the Python API for components running in
    # pyodide in the browser.
    assert "ipymuvue/pyodide/vue.py" in assets
    assert "ipymuvue/__init__.py" in assets
    assert all(isinstance(content, bytes) for content in assets.values())


def test_invalid_components():
    with pytest.raises(TypeError):
        VueWidget(template="<div/>", components={1: "<template/>"})

    with pytest.raises(NotImplementedError):
        VueWidget(template="<div/>", components={"child": 1})


def test_invalid_assets():
    with pytest.raises(TypeError):
        VueWidget(template="<div/>", assets={1: "content"})

    with pytest.raises(NotImplementedError):
        VueWidget(template="<div/>", assets={"a.vue": 1})


def test_slots():
    from ipywidgets import Button

    widget = VueWidget(template="<div><slot/><slot name='other'/></div>")

    default = Button()
    other = Button()

    widget.slot(default)
    widget.slot("other", other)

    assert widget._VueWidget__children == {"default": default, "other": other}

    with pytest.raises(TypeError):
        widget.slot(1, Button())


def test_assets_must_not_replace_ipymuvue():
    with pytest.raises(ValueError, match="shipped with ipymuvue"):
        VueWidget(template="<div/>", assets={"ipymuvue/pyodide/vue.py": "# replaced"})


def test_arguments_are_not_modified():
    components = {"child": "<template><div>child</div></template>"}
    assets = {"Other.vue": "<template><div>other</div></template>"}

    VueWidget(template="<child/>", components=components, assets=assets)

    assert components == {"child": "<template><div>child</div></template>"}
    assert assets == {"Other.vue": "<template><div>other</div></template>"}

    # The same arguments can be used again for another widget.
    VueWidget(template="<child/>", components=components, assets=assets)
