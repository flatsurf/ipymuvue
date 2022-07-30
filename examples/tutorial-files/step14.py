from ipymuvue.pyodide.vue import define_component


component = define_component(
    template=r"""
    <slot>Fallback content</slot>
"""
)
