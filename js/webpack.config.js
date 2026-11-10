// Additional webpack configuration that JupyterLab merges into the
// configuration it uses to build the extension.
const webpack = require("webpack");

module.exports = {
  resolve: {
    alias: {
      // We compile templates in the browser so we need the full build of Vue
      // that includes the template compiler.
      vue$: "vue/dist/vue.esm-bundler.js",
    },
  },
  plugins: [
    // Feature flags of Vue, see https://link.vuejs.org/feature-flags
    new webpack.DefinePlugin({
      // We need the Options API for our implementation of the widget view.
      __VUE_OPTIONS_API__: JSON.stringify(true),
      // Keep devtools support to simplify debugging widgets.
      __VUE_PROD_DEVTOOLS__: JSON.stringify(true),
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: JSON.stringify(false),
    }),
  ],
};
