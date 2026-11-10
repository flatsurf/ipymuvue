**Changed:**

* Changed the build system from the deprecated jupyter-packaging to hatchling
  and hatch-jupyter-builder. Building a wheel now builds the entire frontend
  (`ts/` and `js/`) automatically.

**Fixed:**

* Fixed the license classifier of the Python package which claimed that
  ipymuvue was MIT licensed. It is licensed under GPL-3.0-or-later.
