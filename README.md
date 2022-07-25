# ipyμvue

Reactive Vue 3 widgets for the Jupyter notebook in Python.

Installation
------------

    pip install ipymuvue

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

    jupyter labextension develop --overwrite ipymuvue

Now, start a `jupyter` notebook or `jupyter lab` and verify that the notebooks in `examples/` work correctly.
