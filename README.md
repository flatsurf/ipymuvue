# ipyμvue

Reactive Vue 3 widgets for the Jupyter notebook in Python.

Installation
------------

    pip install ipymuvue

Getting Started
---------------

There is no proper documentation for this project yet, but there are some
[examples/](examples/).

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

Enable the extension in the notebook:

    jupyter nbextension install --py --symlink --overwrite --sys-prefix ipymuvue
    jupyter nbextension enable --py --sys-prefix ipymuvue

Or, enable it in JupyterLab (see #8):

    (cd js && yarn build:labextension)
    jupyter labextension develop --overwrite ipymuvue

Now, start a `jupyter` notebook or `jupyter lab` and verify that the notebooks in `examples/` work correctly.

Any changes you make to the Python code should be picked up automatically. Changes to `ipymuvue.pyodide` become effective by re-creating a widget (all the modules are reloaded in pyodide when a change to these files happens.) Other changes require a kernel restart as usual.

When working with the classic notebook, any changes to the TypeScript/Javascript code, get picked up automatically and become effective once refreshing your browser. In JupyterLab, you need to rebuild the prebuilt extension and refresh the browser:

    (cd js && yarn build:labextension)
