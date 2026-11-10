// Configuration of webpack to build the frontend as an AMD module that
// @jupyter-widgets/html-manager can load to render widgets on static HTML
// pages such as our documentation. Run with `jlpm build:embed`.
const path = require("path");
const webpack = require("webpack");
const { merge } = require("webpack-merge");

module.exports = merge(require("./webpack.config.js"), {
  mode: "production",
  entry: "./lib/index.js",
  output: {
    filename: "index.js",
    path: path.resolve(__dirname, "dist"),
    library: { type: "amd" },
  },
  // The page that embeds the widgets provides the widget base classes.
  externals: ["@jupyter-widgets/base"],
  plugins: [
    // Build a single file so that we do not need to tell webpack where to
    // find additional chunks.
    new webpack.optimize.LimitChunkCountPlugin({ maxChunks: 1 }),
  ],
  performance: { hints: false },
});
