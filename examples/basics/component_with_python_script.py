from ipymuvue.pyodide.vue import define_component

from subcomponent_pure_python import component as subcomponent_pure_python

component = define_component(
    components=dict(
        subcomponentPurePython=subcomponent_pure_python,
        subcomponentWithPythonScript=open('subcomponent-with-python-script.vue'),
    ),
)
