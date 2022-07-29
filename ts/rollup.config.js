// rollup.config.js
import fs from 'fs';
import path from 'path';
import alias from '@rollup/plugin-alias';
import commonjs from '@rollup/plugin-commonjs';
import replace from '@rollup/plugin-replace';
import babel from '@rollup/plugin-babel';
import { terser } from 'rollup-plugin-terser';
import minimist from 'minimist';
import typescript from "@rollup/plugin-typescript";
import { nodeResolve } from '@rollup/plugin-node-resolve';

// Get browserslist config and remove ie from es build targets
const esbrowserslist = fs.readFileSync('./.browserslistrc')
  .toString()
  .split('\n')
  .filter((entry) => entry && entry.substring(0, 2) !== 'ie');

const argv = minimist(process.argv.slice(2));

const projectRoot = path.resolve(__dirname);

const baseConfig = {
  input: 'src/index.ts',
  external: [
    // Declaring "vue" as an external breaks the usage of "template"
    // in JupyterLab telling us that we need to alias vue to
    // vue/dist/vue.esm-bundler.js.
    // 'vue',

    // Declaring "vue/dist/vue.esm-bundler.js" as an external works
    // fine and breaks the esm bundler out of the final distribution
    // for JupyterLab. However, the __VUE_OPTIONS_API__ and
    // __VUE_PROD_DEVTOOLS__ replacements do not happen if we do this
    // and we get warnings on the devoloper console then.
    // 'vue/dist/vue.esm-bundler.js',

    '@jupyter-widgets/base',
    'vue3-sfc-loader',
  ],
  plugins: {
    alias: {
      entries: {
        'vue': 'vue/dist/vue.esm-bundler.js',
      },
    },
    replace: {
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'production'),
      'process.env.ES_BUILD': JSON.stringify('false'),
      // We need the Options API for our implementation of the widget
      // View (but that would be easy to change.)
      // Setting this to "false" only saves 10k/20k in the
      // final output (production/development) which is not quite
      // worth it since we are shipping the huge vue3-sfc-copmiler
      // already anyway.
      '__VUE_OPTIONS_API__': true,
      // Setting this to "false" does not appear to have any real
      // advantage other than making things harder to debug in
      // production builds.
      '__VUE_PROD_DEVTOOLS__': true,
      ... process.env.PYODIDE_CDN ? {
        'PYODIDE_CDN': JSON.stringify(process.env.PYODIDE_CDN),
      } : {},
      'preventAssignment': true,
    },
    typescript: {
      tsconfig: "tsconfig.json",
    },
    vue: {
      css: true,
      template: {
        isProduction: true,
      },
    },
    babel: {
      exclude: 'node_modules/**',
      extensions: ['.js', '.ts', '.vue'],
      babelHelpers: 'bundled',
    },
  },
};

// Customize configs for individual targets
const buildFormats = [];
if (!argv.format || argv.format === 'es') {
  const esConfig = {
    ...baseConfig,
    output: {
      file: 'dist/ipymuvueimplementation.esm.js',
      format: 'esm',
      exports: 'named',
      sourcemap: true,
    },
    plugins: [
      replace({
        ...baseConfig.plugins.replace,
        'process.env.ES_BUILD': JSON.stringify('true'),
      }),
      alias(baseConfig.plugins.alias),
      typescript(baseConfig.plugins.typescript),
      babel({
        ...baseConfig.plugins.babel,
        presets: [
          [
            '@babel/preset-env',
            {
              targets: esbrowserslist,
            },
          ],
        ],
      }),
      commonjs(),
      nodeResolve(),
    ],
  };
  buildFormats.push(esConfig);
}

if (!argv.format || argv.format === 'cjs') {
  const umdConfig = {
    ...baseConfig,
    output: {
      compact: true,
      file: 'dist/ipymuvueimplementation.ssr.js',
      format: 'cjs',
      name: 'ipymuvueimplementation',
      exports: 'named',
      sourcemap: true,
    },
    plugins: [
      replace(baseConfig.plugins.replace),
      alias(baseConfig.plugins.alias),
      typescript(baseConfig.plugins.typescript),
      babel(baseConfig.plugins.babel),
      commonjs(),
      nodeResolve(),
    ],
  };
  buildFormats.push(umdConfig);
}

if (!argv.format || argv.format === 'iife') {
  const unpkgConfig = {
    ...baseConfig,
    output: {
      compact: true,
      file: 'dist/ipymuvueimplementation.min.js',
      format: 'iife',
      name: 'ipymuvueimplementation',
      exports: 'named',
      sourcemap: true,
    },
    plugins: [
      replace(baseConfig.plugins.replace),
      alias(baseConfig.plugins.alias),
      typescript(baseConfig.plugins.typescript),
      babel(baseConfig.plugins.babel),
      commonjs(),
      nodeResolve(),
      terser({
        output: {
          ecma: 5,
        },
      }),
    ],
  };
  buildFormats.push(unpkgConfig);
}

// Export config
export default buildFormats;
