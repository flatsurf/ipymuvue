from vue import define_component, set_default_export

component = define_component(
    template=r"""
        <span>
            Recursive component implemented in Python containing
            <span v-if="depth"> a <component-recursive-in-python :depth="depth - 1" v-if="depth"/></span>
            <span v-else>nothing</span>
        </span>
    """,
    props=["depth"],
    name="component-recursive-in-python")

set_default_export(globals(), component)
