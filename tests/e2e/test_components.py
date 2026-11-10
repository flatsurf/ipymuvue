r"""
End-to-end tests for Vue components used in widgets.
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

STDOUT = "[data-mime-type='application/vnd.jupyter.stdout']"

COUNTER = r"""
<template>
  <button @click="count++">{{ label }}: {{ count }}</button>
</template>
<script setup>
import { ref } from 'vue'

defineProps(['label'])

const count = ref(0)
</script>
"""


def test_component_from_string(notebook):
    cell = notebook.run(f'''
from ipymuvue.widgets import VueWidget

VueWidget(template='<counter label="clicks"/>', components={{"counter": r"""{COUNTER}"""}})
''')

    button = cell.locator("button")
    expect(button).to_have_text("clicks: 0")

    button.click()
    expect(button).to_have_text("clicks: 1")


def test_component_from_file(notebook):
    (notebook.lab.root / "Counter.vue").write_text(COUNTER)

    cell = notebook.run("""
from ipymuvue.widgets import VueWidget

VueWidget(template='<counter label="from file"/>', components={"counter": open("Counter.vue")})
""")

    expect(cell.locator("button")).to_have_text("from file: 0")


def test_component_from_assets(notebook):
    cell = notebook.run(f'''
from ipymuvue.widgets import VueWidget

VueWidget(
    template='<outer/>',
    components={{"outer": "Outer.vue"}},
    assets={{
        "Outer.vue": "<template><counter label='nested'/></template><script>import Counter from './Counter.vue'; export default {{ components: {{ Counter }} }}</script>",
        "Counter.vue": r"""{COUNTER}""",
    }})
''')

    expect(cell.locator("button")).to_have_text("nested: 0")


def test_props_from_traitlets(notebook):
    cell = notebook.run(f'''
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template='<counter :label="label"/>', components={{"counter": r"""{COUNTER}"""}})

    label = Unicode("before").tag(sync=True)

widget = Widget()
widget
''')

    button = cell.locator("button")
    expect(button).to_have_text("before: 0")

    button.click()
    notebook.run('widget.label = "after"')

    # The prop changes, but the state of the component is preserved.
    expect(button).to_have_text("after: 1")


def test_component_in_python(notebook):
    r"""
    Test a component that is implemented in Python and executed in the
    browser by pyodide.
    """
    (notebook.lab.root / "counter.py").write_text(r'''
from ipymuvue.pyodide.vue import define_component, ref, computed


def setup(props, context):
    count = ref(0)
    double = computed(lambda: 2 * count.value)

    def increment(event):
        count.value += 1

    return locals()


component = define_component(
    setup=setup,
    props=["label"],
    template=r"""<button @click="increment">{{ label }}: {{ count }}, {{ double }}</button>""",
)
''')

    cell = notebook.run("""
from ipymuvue.widgets import VueWidget

VueWidget(template='<counter label="python"/>', components={"counter": open("counter.py")})
""")

    # Loading pyodide from the CDN can take a long time.
    button = cell.locator("button")
    expect(button).to_have_text("python: 0, 0", timeout=120_000)

    button.click()
    expect(button).to_have_text("python: 1, 2")


def test_rpc(notebook):
    r"""
    Test calling methods of components from Python.
    """
    cell = notebook.run(r'''
from ipymuvue.widgets import VueWidget

widget = VueWidget(template='<calculator ref="calculator"/>', components={"calculator": r"""
<template><div>calculator</div></template>
<script setup>
function add(a, b) { return a + b }
function fail() { throw Error("failed in the browser") }
defineExpose({ add, fail })
</script>
"""})
widget
''')

    expect(cell).to_contain_text("calculator")

    output = notebook.run("print(await widget['calculator'].add(1, 2))")
    expect(output.locator(STDOUT)).to_have_text("[3]\n")

    output = notebook.run("""
from ipymuvue.widgets.references import InvocationError

try:
    await widget['calculator'].fail()
except InvocationError as e:
    print(e)
""")
    expect(output.locator(STDOUT)).to_have_text("failed in the browser\n")
