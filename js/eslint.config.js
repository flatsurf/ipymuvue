// Configuration of ESLint, run with `jlpm lint` or `pixi run lint`.
const { defineConfig } = require("eslint/config");
const js = require("@eslint/js");
const tseslint = require("typescript-eslint");

module.exports = defineConfig(
  { ignores: ["lib/", "node_modules/", ".yarn/"] },
  js.configs.recommended,
  tseslint.configs.recommended,
  {
    files: ["*.js"],
    languageOptions: { sourceType: "commonjs", globals: { require: "readonly", module: "writable" } },
    rules: { "@typescript-eslint/no-require-imports": "off" },
  },
  {
    rules: {
      // We need to interface with lots of untyped JavaScript, in particular
      // with Python objects proxied by Pyodide.
      "@typescript-eslint/no-explicit-any": "off",
      // Vue's Options API rebinds `this` so we need to capture the outer `this`.
      "@typescript-eslint/no-this-alias": "off",
      // Unused arguments are fine if their name says so.
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },
);
