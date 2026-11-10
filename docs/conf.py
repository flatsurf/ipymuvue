# Configuration of the Sphinx documentation, build with `pixi run docs`.
#
# The documentation renders the notebooks in examples/. We execute them while
# building and embed the state of their widgets so that the widgets work on
# the static pages (as long as they do not need to talk to a Python kernel.)

import pathlib
import shutil

from ipymuvue.version import __version__

project = "ipyμvue"
copyright = "2022, Julian Rüth"
author = "Julian Rüth"
release = __version__

extensions = ["myst_nb"]

html_theme = "furo"
html_title = f"ipyμvue {release}"
html_static_path = ["_static"]

exclude_patterns = ["_build"]

# Copy the examples into the documentation since the notebooks load their
# assets from paths relative to the notebook.
# RPC.md cannot run without a browser since it waits for the frontend.
root = pathlib.Path(__file__).parent
shutil.rmtree(root / "examples", ignore_errors=True)
shutil.copytree(
    root.parent / "examples",
    root / "examples",
    ignore=shutil.ignore_patterns("README.md", "RPC.md"),
)

# The notebooks are written in different flavors of Markdown which jupytext
# detects from their metadata.
nb_custom_formats = {".md": ["jupytext.reads", {"fmt": "md"}]}

nb_execution_mode = "force"
nb_execution_timeout = 600
nb_execution_raise_on_error = True
nb_execution_show_tb = True

# Load the frontend of ipymuvue from this site instead of from a CDN when
# rendering the embedded widgets, see js/webpack.embed.config.js.
nb_ipywidgets_js = {
    "https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js": {
        "integrity": "sha256-Ae2Vz/4ePdIu6ZyI/5ZGsYnb+m0JlOmKPjt6XZ9JJkA=",
        "crossorigin": "anonymous",
    },
    "ipymuvue-embed.js": {},
    "https://cdn.jsdelivr.net/npm/@jupyter-widgets/html-manager@1.0.15/dist/embed-amd.js": {
        "data-jupyter-widgets-cdn": "https://cdn.jsdelivr.net/npm/",
        "crossorigin": "anonymous",
    },
}


def setup(app):
    # Ship the frontend built by `jlpm build:embed`.
    def copy_frontend(app, exception):
        if exception is None:
            target = pathlib.Path(app.outdir) / "_static" / "ipymuvue"
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy(root.parent / "js" / "dist" / "index.js", target / "index.js")

    app.connect("build-finished", copy_frontend)
