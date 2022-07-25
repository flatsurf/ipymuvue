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
    cd ../js
    yarn

Start the rollup/typescript build:

    cd ts
    yarn link  # only necessary the first time
    yarn cross-env NODE_ENV=development rollup --config rollup.config.js --watch --parallel

In another console, start the webpack bundling:

    cd js
    yarn link ipymuvueimplementation  # only necessary the first time
    yarn watch --progress

If you had not done so before, install a development version of ipymuvue:

    pip uninstall ipymuvue  # if you had a regular ipymuvue installed
    pip install -e .

Enable the extension in the notebook:

    jupyter nbextension install --py --symlink --overwrite --sys-prefix ipymuvue
    jupyter nbextension enable --py --sys-prefix ipymuvue

Or, enable it in JupyterLab (see #8):

    jupyter labextension develop --overwrite ipymuvue
