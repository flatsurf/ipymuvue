r"""
End-to-end tests for synchronizing state between Python and the browser.
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

from playwright.sync_api import expect

# The example from the README.
HELLO = r'''
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <div>
                <h1 @click="audience += '!'" @click.right.prevent.stop="rclick()" style="border: solid 1px blue; text-align: center; padding: 20px; user-select: none">
                    Hello {{ audience }}!
                </h1>
            </div>
        """)

    audience = Unicode("World").tag(sync=True)

    @VueWidget.callback
    def rclick(self):
        self.audience = '¡' + self.audience

widget = Widget()
widget
'''


def test_hello_world(notebook):
    title = notebook.run(HELLO).locator("h1")
    expect(title).to_have_text("Hello World!")

    # Left clicks are handled in the browser.
    title.click()
    expect(title).to_have_text("Hello World!!")

    # Right clicks are handled by a callback in Python.
    title.click(button="right")
    expect(title).to_have_text("Hello ¡World!!")

    # The state is synchronized to Python.
    output = notebook.run("print(widget.audience)").locator(".jp-OutputArea-output")
    expect(output).to_have_text("¡World!")

    # The state can be changed from Python.
    notebook.run("widget.audience = 'Jupyter'")
    expect(title).to_have_text("Hello Jupyter!")


def test_multiple_views(notebook):
    first = notebook.run(HELLO).locator("h1")
    second = notebook.run("widget").locator("h1")

    expect(first).to_have_text("Hello World!")
    expect(second).to_have_text("Hello World!")

    # A change in one view is reflected in all the views.
    second.click()
    expect(first).to_have_text("Hello World!!")
    expect(second).to_have_text("Hello World!!")


def test_capture_output(notebook):
    cell = notebook.run(r'''
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""<button @click="greet('World')">Greet</button>""")

    @VueWidget.callback
    def greet(self, audience):
        print(f"Hello {audience}!")

Widget()
''')

    cell.locator("button").click()

    # The output of callbacks is shown underneath the widget.
    stdout = cell.locator("[data-mime-type='application/vnd.jupyter.stdout']")
    expect(stdout).to_have_text("Hello World!\n")


def test_slots(notebook):
    cell = notebook.run(r'''
import ipywidgets
from ipymuvue.widgets import VueWidget

widget = VueWidget(template=r"""
    <div>
        <h3>default</h3>
        <slot/>
        <h3>named</h3>
        <slot name="named"/>
    </div>
""")

widget.slot(ipywidgets.Button(description="default button"))
widget.slot("named", ipywidgets.Button(description="named button"))

widget
''')

    expect(cell.get_by_role("button", name="default button")).to_be_visible()
    expect(cell.get_by_role("button", name="named button")).to_be_visible()

    # Slots can be replaced.
    notebook.run('widget.slot(ipywidgets.Button(description="replaced button"))')
    expect(cell.get_by_role("button", name="replaced button")).to_be_visible()
    expect(cell.get_by_role("button", name="default button")).to_have_count(0)
