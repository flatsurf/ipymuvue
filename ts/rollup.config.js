// rollup.config.js
import fs from 'fs';
import path from 'path';
import vue from 'rollup-plugin-vue';
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
    'vue',
    '@jupyter-widgets/base',
    'vue3-sfc-loader',
  ],
  plugins: {
    preVue: [
      alias({
        resolve: ['.js', '.ts', '.vue'],
        entries: {
          '@': path.resolve(projectRoot, 'src'),
        },
      }),
    ],
    replace: {
      'process.env.NODE_ENV': JSON.stringify('production'),
      'process.env.ES_BUILD': JSON.stringify('false'),
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
      file: 'dist/ipyvue3implementation.esm.js',
      format: 'esm',
      exports: 'named',
      sourcemap: true,
    },
    plugins: [
      replace({
        ...baseConfig.plugins.replace,
        'process.env.ES_BUILD': JSON.stringify('true'),
      }),
      typescript(baseConfig.plugins.typescript),
      ...baseConfig.plugins.preVue,
      vue(baseConfig.plugins.vue),
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
      file: 'dist/ipyvue3implementation.ssr.js',
      format: 'cjs',
      name: 'ipyvue3implementation',
      exports: 'named',
      sourcemap: true,
    },
    plugins: [
      replace(baseConfig.plugins.replace),
      typescript(baseConfig.plugins.typescript),
      ...baseConfig.plugins.preVue,
      vue({
        ...baseConfig.plugins.vue,
        template: {
          ...baseConfig.plugins.vue.template,
          optimizeSSR: true,
        },
      }),
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
      file: 'dist/ipyvue3implementation.min.js',
      format: 'iife',
      name: 'ipyvue3implementation',
      exports: 'named',
      sourcemap: true,
    },
    plugins: [
      replace(baseConfig.plugins.replace),
      typescript(baseConfig.plugins.typescript),
      ...baseConfig.plugins.preVue,
      vue(baseConfig.plugins.vue),
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
