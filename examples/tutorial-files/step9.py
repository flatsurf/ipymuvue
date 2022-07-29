from ipymuvue.pyodide.vue import define_component, ref, on_mounted


def setup(props, context):
    p = ref(None)
    q = ref(None)

    @on_mounted
    def update_p():
        p.value["textContent"] = "mounted!"
        q.value.textContent = "mounted!"

    return locals()


component = define_component(setup=setup, template=r"""
    <p ref="p">hello</p>
    <p ref="q">hello</p>
""")
