from ipymuvue.pyodide.vue import define_component, ref


def setup(props, context):
    text = ref('')

    return locals()


component = define_component(setup=setup, template=r"""
    <input v-model="text" placeholder="Type here">
    <p>{{ text }}</p>
""")
