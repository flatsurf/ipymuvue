from ipymuvue.pyodide.vue import define_component, ref, reactive, vue_compatible


def setup(props, context):
    # We cannot say
    #   counter = reactive({"count": 0})
    # since we refuse to create a proxy of a native Python object. If we want
    # to use `reactive`, we need to explicitly create a JavaScript object:
    counter = vue_compatible({"count": 0}, reference=False)
    counter = reactive(counter)

    message = ref("Hello World!")

    return locals()


component = define_component(setup=setup, template=r"""
<h4>{{ message }}</h4>
<p>Count is: {{ counter.count }}</p>
""")
