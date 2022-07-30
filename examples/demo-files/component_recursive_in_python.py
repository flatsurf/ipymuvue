from ipymuvue.pyodide.vue import define_component

component = define_component(
    template=r"""
        <span>
            a recursive component containing
            <span v-if="depth"><component-recursive-in-python :depth="depth - 1" v-if="depth"/></span>
            <span v-else>nothing</span>
        </span>
    """,
    props=["depth"],
    name="component-recursive-in-python",
)
