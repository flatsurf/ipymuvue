from ipymuvue.pyodide.vue import define_component, ref


def setup(props, context):
    count = ref(0)

    # In JavaScript, undeclared arguments are automatically ignored. Here, we
    # need to specify that we are given one argument, the details of the click
    # event.
    def increment(event):
        nonlocal count
        count.value += 1

    return locals()


component = define_component(
    setup=setup,
    template=r"""
    <button @click="increment">count is: {{ count }}</button>
""",
)
