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

We use [pixi](https://pixi.sh) to manage all the dependencies needed for
development, including `node` and `yarn`. Once you have installed pixi, start
JupyterLab with a development version of ipymuvue in the `examples/` directory:

    pixi run lab

Any changes you make to the Python code should be picked up automatically. Changes to `ipymuvue.pyodide` become effective by re-creating a widget (all the modules are reloaded in pyodide when a change to these files happens.) Other changes require a kernel restart as usual.

Any changes to the TypeScript/Javascript code become effective after you rebuild the prebuilt extension and refresh the browser:

    pixi run build-js

To run the unit tests and the end-to-end tests (which run the widgets in
JupyterLab in a headless browser), run:

    pixi run test
    pixi run test-e2e

To see what the end-to-end tests are doing, run `pixi run test-e2e --headed
--slowmo 500`. Note that playwright might need some extra system libraries to
run the browser; on Debian and Ubuntu, `pixi run playwright install-deps
chromium` installs them.

To build the wheel and source distribution of ipymuvue, run:

    pixi run build

To create a new release, add a file describing your changes to `news/` and run:

    pixi run release <version>

If you do not want to use pixi, you need Python, JupyterLab 4, `node`, and
`yarn` (version 1). Then `pip install -e .` builds and installs ipymuvue and
`(cd js && yarn build)` rebuilds the frontend.


Related Projects
----------------

* [ipyvue](https://github.com/widgetti/ipyvue) heavily inspired this package; ipyvue builds on Vue 2, it does not ship a full SFC compiler, it does not have support for external packages and it does not support defining components that completely run on the client. However, it has quite some extra features for the actual widget such as allowing replacement of templates, attaching to lifecycle hooks, defining `<style>` blocks, …
