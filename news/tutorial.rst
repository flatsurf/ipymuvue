**Added:**

* Added equivalent implementations to the official vuejs.org [tutorial](https://vuejs.org/tutorial/) to `examples/`.
* Added function to expose lifecycle hooks, such as `on_mounted`, to the Python pyodide API.
* Added function to expose `reactive()` to the Python pyodide API.

**Fixed:**

* Fixed writing to wrapped arrays in the pyodide API.
* Allow watching non-callable reactive items directly in the pyodide API.
