// Tell require.js where to find the frontend of ipymuvue so that the
// @jupyter-widgets/html-manager can render our widgets, see docs/conf.py.
require.config({
  paths: {
    ipymuvue: document.currentScript.src.replace(
      /ipymuvue-embed\.js.*$/,
      "ipymuvue/index",
    ),
  },
});
