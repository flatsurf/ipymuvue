import os.path

from ipymuvue.pyodide.vue import define_component


component = define_component(
    template=r"""
    <ChildComp />
    """,
    components={
        "ChildComp": open("ChildComp.vue"),
    },
)
