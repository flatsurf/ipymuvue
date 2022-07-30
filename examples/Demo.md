---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.0
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

# Basic Reactivity

A left click on the title is handled by JavaScript in the frontend, a right click is handled by Python in the backend.

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <div>
                <h1 @click="audience += '!'" @click.right.prevent.stop="rclick()" style="border: solid 1px blue; text-align: center; padding: 20px; user-select: none">
                    Hello {{ audience }}!
                </h1>
            </div>
        """)
        
    audience = Unicode("World").tag(sync=True)
    
    @VueWidget.callback
    def rclick(self):
        self.audience = '¡' + self.audience
        
    
widget = Widget()
widget
```

The state of the widget is available from Python:

```{code-cell} ipython3
widget.audience
```

The state of the widget can be manipulated directly from Python:

```{code-cell} ipython3
widget.audience = "Jupyter"
```

# Subcomponents

Subcomponents can be implemented in JavaScript or in Python in a variety of ways.

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <div>
                <h3>A component loaded from a string</h3>
                <component-from-string/>
                
                <h3>A component loaded from a file</h3>
                <component-from-file/>
                
                <h3>A component from a string in the assets dict</h3>
                <component-from-asset-string/>
                
                <h3>A component from a file in the assets dict</h3>
                <component-from-asset-file/>
                
                <h3>A component whose logic is implemented in Python</h3>
                <component-with-python-script/>
                
                <h3>A recursive component whose logic is implemented in Python</h3>
                <component-recursive-with-python :depth="23"/>
                
                <h3>A recursive component purely in Python</h3>
                <component-recursive-in-python :depth="3"/>
            </div>
        """, components={
            "component-from-string": "<template><div>Component from String</div></template>",
            "component-from-file": open("demo-files/ComponentFromFile.vue"),
            "component-from-asset-string": "ComponentFromAssetString.vue",
            "component-from-asset-file":"ComponentFromAssetFile.vue",
            "component-with-python-script": open("demo-files/ComponentWithPythonScript.vue"),
            "component-recursive-with-python": open("demo-files/ComponentRecursiveWithPython.vue"),
            "component-recursive-in-python": open("demo-files/component_recursive_in_python.py"),
        }, assets={
            "ComponentFromAssetString.vue": "<template><div>Component from an Asset String</div></template>",
            "ComponentFromAssetFile.vue": open("demo-files/ComponentFromFile.vue"),
            "component_with_python_script.py": open("demo-files/component_with_python_script.py"),
            "SubcomponentWithPythonScript.vue": open("demo-files/SubcomponentWithPythonScript.vue"),
            "subcomponent_with_python_script.py": open("demo-files/subcomponent_with_python_script.py"),
            "subcomponent_pure_python.py": open("demo-files/subcomponent_pure_python.py"),
            "component_recursive_with_python.py": open("demo-files/component_recursive_with_python.py")
        })
        
    
widget = Widget()
widget
```

# Importing Remote Subcomponents
Note the <span style="color:red">security implications</span>: such external JavaScript code (as any JavaScript code that other widgets use) could in principle send arbitrary commands to the running kernel, i.e., it could run arbitrary commands on your host machine. By using such external resources, you are entrusting the system to the external package author and the CDN from which you are downloading the package. The latter can be fixed by providing the package bundled with your widget and provisioning it as an asset.

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Dict

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <div>
                <remote-network-graph :nodes="nodes" :edges="edges" />
            </div>
        """, components={
            "remote-network-graph": open("demo-files/RemoteNetworkGraph.vue"),
        })
        
    nodes = Dict({
        "A": { "name": "A"},
        "B": { "name": "B"},
        "C": { "name": "C"},
        "D": { "name": "D"},
    }).tag(sync=True)
    
    edges = Dict({
        "AB": { "source": "A", "target": "B"},
        "BC": { "source": "B", "target": "C"},
        "CD": { "source": "C", "target": "D"},
    }).tag(sync=True)
    
widget = Widget()
widget
```

# Nested Widgets

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <div style="border: 1px solid blue">
                <h3>An ipywidgets Text Area:</h3>
                <slot/>
                <h3>The same Text Area</h3>
                <slot/>
                <h3>Another Text Area</h3>
                <slot name="secondary"/>
            </div>
        """)        
    
widget = Widget()

import ipywidgets
widget.slot(ipywidgets.Textarea())
widget.slot("secondary", ipywidgets.Textarea())

widget
```
