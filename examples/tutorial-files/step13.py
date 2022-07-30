from ipymuvue.pyodide.vue import define_component


def setup(props, context):
    context.emit("response", "hello from child")

    return locals()


component = define_component(
    setup=setup,
    template=r"""
  <h4>Child component</h4>
""",
)
