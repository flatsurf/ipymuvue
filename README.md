# ipyμvue

Reactive Vue 3 widgets for the Jupyter notebook in Python.

Installation
------------

    pip install ipymuvue

Getting Started
---------------

There is no proper documentation for this project yet, but there are some
[examples/](examples/).

To verify that your installation works correctly, open a Jupyter notebook and execute the following example:

```py
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

If you see a `Hello World` message, then things have been setup correctly.

Note that the **classic** Jupyter notebook (i.e., version <7) is not supported by this extension. If in doubt, use `jupyter lab` to launch your notebooks.

Development
-----------

Get a local copy of this package:

    git clone https://github.com/flatsurf/ipymuvue.git
    cd ipymuvue

Install development dependencies:

    cd ts
    yarn
    yarn link
    cd ../js
    yarn link ipymuvueimplementation
    yarn
    cd ..

Start the rollup/typescript build:

    cd ts
    yarn dev

In another console, start the webpack bundling:

    cd js
    yarn dev

If you had not done so before, install a development version of ipymuvue:

    pip uninstall ipymuvue  # if you had a regular ipymuvue installed
    pip install -e .

Enable the extension in JupyterLab and the notebook (version 7 required):

    (cd js && yarn build)
    jupyter labextension develop --overwrite ipymuvue

Now, start a `jupyter` notebook or `jupyter lab` and verify that the notebooks in `examples/` work correctly.

Any changes you make to the Python code should be picked up automatically. Changes to `ipymuvue.pyodide` become effective by re-creating a widget (all the modules are reloaded in pyodide when a change to these files happens.) Other changes require a kernel restart as usual.

Any changes to the TypeScript/Javascript code become effective after you rebuild the prebuilt extension and refresh the browser:

    (cd js && yarn build)


Related Projects
----------------

* [ipyvue](https://github.com/widgetti/ipyvue) heavily inspired this package; ipyvue builds on Vue 2, it does not ship a full SFC compiler, it does not have support for external packages and it does not support defining components that completely run on the client. However, it has quite some extra features for the actual widget such as allowing replacement of templates, attaching to lifecycle hooks, defining `<style>` blocks, …
