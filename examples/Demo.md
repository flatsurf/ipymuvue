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

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Dict, Unicode, Integer

class Widget(VueWidget):
    def __init__(self, render, xmin=0, ymin=0, xmax=1, ymax=1):
        super().__init__(template=r"""
            <draggable-plot :current="plot" @refresh="refresh" />
        """, components={
            "draggable-plot": open("demo-files/DraggablePlot.vue"),
        }, assets={
            "Plot.vue": open("demo-files/Plot.vue"),
        })
        
        self._render = render
        
        self.refresh(dict(
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
        ))
        
    plot = Dict().tag(sync=True)
        
    @VueWidget.callback
    def refresh(self, bounds):
        import matplotlib
        import matplotlib.pyplot
        backend = matplotlib.get_backend()
        matplotlib.use('agg')
        try:
            figure=matplotlib.pyplot.figure(dpi=96)
            self._render(bounds).matplotlib(figure=figure, **bounds)
            figure.tight_layout()
            figure.canvas.draw()
            canvas = figure.canvas

            from io import BytesIO
            raw = BytesIO()

            canvas.print_png(raw)
            raw.seek(0)
            
            bbox = figure.axes[0].get_window_extent(figure.canvas.get_renderer()).get_points()
            width, height = figure.canvas.get_width_height()
            
            from sage.all import matrix, vector
            A = matrix([
                [(bbox[1][0] - bbox[0][0]) / (bounds["xmax"] - bounds["xmin"]), 0, bbox[0][0]],
                [0, -(bbox[1][1] - bbox[0][1]) / (bounds["ymax"] - bounds["ymin"]), bbox[1][1]],
                [0, 0, 1]
            ]) * matrix([
                [1, 0, -bounds["xmin"]],
                [0, 1, -bounds["ymin"]],
                [0, 0, 1]
            ])

            B = ~A
            
            xmin, ymin, _ = B * vector([0, height, 1])
            xmax, ymax, _ = B * vector([width, 0, 1])
            
            import base64
            self.plot = dict(
                png=base64.b64encode(raw.read()).decode('utf-8'),
                bounds=dict(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax))

            matplotlib.pyplot.close(figure)            
        finally:
            matplotlib.use(backend)
            
def render(bounds):
    from sage.all import plot, var, sin
    x = var('x')
    return plot(sin(x) + x**2/64, **bounds)
            
widget = Widget(render)
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
