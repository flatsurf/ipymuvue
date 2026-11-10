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
development, including `node`. Once you have installed pixi, start
JupyterLab with a development version of ipymuvue in the `examples/` directory:

    pixi run lab

Some examples, such as the graph editor, need a SageMath kernel. Since the
SageMath kernel only works when JupyterLab runs in the same environment as
SageMath, use `pixi run -e sage lab` for these (not available on Windows.)

Any changes you make to the Python code should be picked up automatically. Changes to `ipymuvue.pyodide` become effective by re-creating a widget (all the modules are reloaded in pyodide when a change to these files happens.) Other changes require a kernel restart as usual.

The frontend is written in TypeScript in `js/src/`. To rebuild it
automatically whenever you change a file, run in another terminal:

    pixi run watch

Changes become effective once the rebuild has finished and you refresh the
page in the browser. (To build the frontend once, run `pixi run build-js`.)

To run the unit tests and the end-to-end tests (which run the widgets in
JupyterLab in a headless browser), run:

    pixi run test
    pixi run test-e2e

To see what the end-to-end tests are doing, run `pixi run test-e2e --headed
--slowmo 500`. Note that playwright might need some extra system libraries to
run the browser; on Debian and Ubuntu, `pixi run playwright install-deps
chromium` installs them.

We check the Python code with [ruff](https://docs.astral.sh/ruff/) and the
TypeScript code with [ESLint](https://eslint.org/):

    pixi run lint

To run these checks automatically before each commit, run `pixi run
pre-commit install`.

To build the wheel and source distribution of ipymuvue, run:

    pixi run build

Changelog
---------

Every pull request that changes something users of ipymuvue might care about
should add a file to `news/` describing the change. The name of the file is
`<some-name>.<category>.rst` where the category is one of `added`, `changed`,
`removed`, or `fixed`, e.g., `news/slots.fixed.rst`:

    Fixed replacing the widget in a slot with `VueWidget.slot()`.

These files are collected into the `ChangeLog` when making a release. To see
what the next entry in the `ChangeLog` is going to look like, run `pixi run -e
release towncrier build --draft --version next`.

Releasing
---------

To release a new version of ipymuvue, say 1.2.3:

1. Make sure that your copy of the master branch is identical to the master
   branch on GitHub and that all the tests passed on GitHub.

2. Run `pixi run release-prepare 1.2.3`. This writes the `news/` into the
   `ChangeLog`, updates the version number everywhere, commits these changes
   as "Release 1.2.3" and creates a tag 1.2.3. (Nothing is pushed yet. If
   something looks wrong, delete the tag with `git tag -d 1.2.3`, drop the
   commit with `git reset --hard HEAD~1`, and start over.)

3. Push the master branch and then the tag: `git push origin master` and `git
   push origin 1.2.3`.

Once GitHub sees the tag, the "Build and publish to PyPI" workflow builds
ipymuvue, uploads it to [PyPI](https://pypi.org/project/ipymuvue/), and
creates a [release on GitHub](https://github.com/flatsurf/ipymuvue/releases)
with the new section of the `ChangeLog`. The workflow refuses to publish if
the tag does not match the version of ipymuvue or if the tag is not on the
master branch.

Note that version 0.6.0 was released to PyPI from a commit that never made it
to the master branch, so the next release has to be at least 0.7.0.

If you do not want to use pixi, you need Python, JupyterLab 4 (which comes
with `jlpm`), and `node`. Then `pip install -e .` builds and installs ipymuvue,
`(cd js && jlpm build)` rebuilds the frontend, and `jupyter labextension
develop --overwrite .` makes JupyterLab use your build of the frontend.


Related Projects
----------------

* [ipyvue](https://github.com/widgetti/ipyvue) heavily inspired this package; ipyvue builds on Vue 2, it does not ship a full SFC compiler, it does not have support for external packages and it does not support defining components that completely run on the client. However, it has quite some extra features for the actual widget such as allowing replacement of templates, attaching to lifecycle hooks, defining `<style>` blocks, …
