from ipymuvue.pyodide.vue import define_component, String


component = define_component(
    template=r"""
    <h4>{{ msg || "No props passed yet" }}</h4>
    """,
    props={"msg": String},
)
