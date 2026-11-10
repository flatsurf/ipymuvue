Changed components written in Python to run on Pyodide 314.0.7, i.e., Python
3.14, instead of a preview release of Pyodide 0.21 with Python 3.10.
Components written in Python now need to import the submodules of `pyodide`
they use explicitly, e.g., `import pyodide.http` to use `pyodide.http.pyfetch`.
