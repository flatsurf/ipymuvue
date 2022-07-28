---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.0
kernelspec:
  display_name: SageMath 9.6
  language: sage
  name: sagemath
---

# Interactive Graph Editor

We're going to build an interactive editor for a SageMath graph. The graph will be displayed as an SVG, roughly like the following.

```{code-cell} ipython3
from ipywidgets import HTML

svg = HTML(r"""
<svg width="300" height="300">
    <line x1="20" y1="150" x2="280" y2="150" stroke="black" stroke-width="2px" />
    <line x1="20" y1="150" x2="150" y2="50" stroke="black" stroke-width="2px" />
    <line x1="150" y1="50" x2="280" y2="150" stroke="black" stroke-width="2px" />
    <circle cx="20" cy="150" r="6" fill="cornflowerblue"/>
    <circle cx="280" cy="150" r="6" fill="cornflowerblue"/>
    <circle cx="150" cy="50" r="6" fill="cornflowerblue"/>
</svg>
""")
svg
```

## Displaying a Graph

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Unicode, Dict, Int, List, Float, Tuple

class GraphEditor0(VueWidget):
    def __init__(self, graph):
        super().__init__(self.template)
        
        self.graph = graph
        
    template = r"""
    <svg :width="width" :height="height">
        <line v-for="(edge, i) of edges" :key="i" stroke="black" stroke-width="2px"
            :x1="positions[edge[0]][0]" :y1="positions[edge[0]][1]"
            :x2="positions[edge[1]][0]" :y2="positions[edge[1]][1]"
        />
        <circle v-for="vertex of vertices" :key="vertex" r="6" fill="cornflowerblue"
            :cx="positions[vertex][0]"
            :cy="positions[vertex][1]"
        />
    </svg>
    """

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, value):
        self._graph = value

        pos = value.get_pos()
        bbox = self.bbox()
        
        with self.hold_sync():
            self.vertices = list(pos.keys())

            self.positions = {v: (
                self.width * (pos[v][0] - bbox[0][0]) / (bbox[0][1] - bbox[0][0]),
                self.height * (pos[v][1] - bbox[1][0]) / (bbox[1][1] - bbox[1][0])
                ) for v in pos}

            self.edges = [(source, target) for (source, target, label) in value.edges()]
        
    def bbox(self):
        pos = self.graph.get_pos()
        xs = [xy[0] for xy in pos.values()]
        ys = [xy[1] for xy in pos.values()]

        bbox = [
            [min(xs), max(xs)],
            [min(ys), max(ys)]
        ]

        bbox[0][0] -= (bbox[0][1] - bbox[0][0]) / 64
        bbox[0][1] += (bbox[0][1] - bbox[0][0]) / 64
        bbox[1][0] -= (bbox[1][1] - bbox[1][0]) / 64
        bbox[1][1] += (bbox[1][1] - bbox[1][0]) / 64

        return bbox

    width = Int(600R).tag(sync=True)
    height = Int(600R).tag(sync=True)

    # A list of vertex ids. (Vertices can be more than just integers in SageMath, but let's pretend they are all integers.)
    vertices = List(Int()).tag(sync=True)

    # a list of (source, target) vertices
    edges = List(Tuple(Int(), Int())).tag(sync=True)
    
    # coordinates of the vertices
    positions = Dict(Tuple(Float(), Float()), Int()).tag(sync=True)

graph = graphs.BuckyBall()

widget = GraphEditor0(graph)
widget
```

## Interacting with the Graph

Right clicking on a vertex deletes it. Right clicking somewhere else relayouts the graph.

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Unicode, Dict, Int, List, Float, Tuple

class GraphEditor1(GraphEditor0):
    template = r"""
    <svg :width="width" :height="height" @click.right.prevent="relayout">
        <line v-for="(edge, i) of edges" :key="i" stroke="black" stroke-width="2px"
            :x1="positions[edge[0]][0]" :y1="positions[edge[0]][1]"
            :x2="positions[edge[1]][0]" :y2="positions[edge[1]][1]"
        />
        <g v-for="vertex of vertices" :key="vertex"
            style="cursor: pointer"
            @click.right.prevent.stop="erase_vertex(vertex)">
            <circle r="6" fill="cornflowerblue"
                :cx="positions[vertex][0]"
                :cy="positions[vertex][1]"/>
            <circle r="18" fill="transparent"
                :cx="positions[vertex][0]"
                :cy="positions[vertex][1]"/>
        </g>
            
        />
    </svg>
    """
    
    @VueWidget.callback
    def erase_vertex(self, vertex):
        graph = self.graph
        graph.delete_vertex(int(vertex))
        self.graph = graph

    @VueWidget.callback
    def relayout(self, _):
        graph = self.graph
        graph.set_pos(graph.layout('spring'))
        self.graph = graph


graph = graphs.BuckyBall()

widget = GraphEditor1(graph)
widget
```

## Dragging Vertices

Change the position of the vertices by dragging them.

Listening to mouse move events inside the backend code is not a great idea (we'd need to serialize and deserialize the state at 60 fps, send it back and forth between frontend and backend.) So, we would like to run that dragging code on the frontend directly.

The recommended way to do this, is to write proper Vue components. We get the best development experience by writing these components in a separate project that uses standard Vue tooling and then load these components.

For prototyping, it's best to create `.vue` files locally, as we do in the following example:

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Unicode, Dict, Int, List, Float, Tuple

class GraphEditor2(GraphEditor1):
    def __init__(self, graph):
        VueWidget.__init__(self, self.template, components=self.components)
        self.graph = graph
    
    template = r"""
        <interactive-graph :vertices="vertices" :edges="edges" :positions="positions" :width="width" :height="height"
            @vertex-rclick="erase_vertex"
            @rclick="relayout(null)" />
    """
    
    components = {
        "interactive-graph": open("interactive-graph.vue")
    }


graph = graphs.BuckyBall()

widget = GraphEditor2(graph)
widget
```

We can, however, also implement things purely in Python. Note that this is **highly experimental**.

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Unicode, Dict, Int, List, Float, Tuple

class GraphEditor2(GraphEditor1):
    def __init__(self, graph):
        VueWidget.__init__(self, self.template, components=self.components)
        self.graph = graph
    
    template = r"""
        <interactive-graph :vertices="vertices" :edges="edges" :positions="positions" :width="width" :height="height"
            @vertex-rclick="erase_vertex"
            @dragged="dragged"
            @rclick="relayout(null)" />
    """
    
    components = {
        "interactive-graph": open("interactive-graph.py")
    }
    
    @VueWidget.callback
    def dragged(self, vertex, x, y):
        graph = self.graph
        pos = graph.get_pos()
        
        bbox = self.bbox()
        pos.update({vertex: (
            x/self.width * (bbox[0][1] - bbox[0][0]) + bbox[0][0],
            y/self.height * (bbox[1][1] - bbox[1][0]) + bbox[1][0],
        )})
        graph.set_pos(pos)
        self.graph = graph


graph = graphs.BuckyBall()

widget = GraphEditor2(graph)
widget
```

Finally, we can use a mix of `.vue` and `.py` files to use JavaScript packages in Python. This is equally **highly experimental**.

```{code-cell} ipython3
from ipymuvue.widgets import VueWidget
from traitlets import Unicode, Dict, Int, List, Float, Tuple

class GraphEditor3(GraphEditor1):
    def __init__(self, graph):
        VueWidget.__init__(self, self.template, components=self.components, assets=self.assets)
        self.graph = graph
    
    template = r"""
        <interactive-graph :vertices="vertices" :edges="edges" :positions="positions" :width="width" :height="height"
            @vertex-rclick="erase_vertex"
            @rclick="relayout(null)" />
    """
    
    components = {
        "interactive-graph": open("interactive-graph-animated.vue")
    }
    
    assets = {
        "interactive-graph-animated.py": open("interactive-graph-animated.py"),
    }


graph = graphs.BuckyBall()

widget = GraphEditor3(graph)
widget
```
