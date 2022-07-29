from ipymuvue.pyodide.vue import define_component, ref


def setup(props, context):
    title_class = ref('title')

    return locals()


component = define_component(setup=setup, template=r"""
    <h4 :class="title_class">Make me red</h4>
""")
