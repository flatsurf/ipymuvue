/* ******************************************************************************
 * Copyright (c) 2022 Julian Rüth <julian.rueth@fsfe.org>
 *
 * ipymuvue is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * ipymuvue is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with ipymuvue. If not, see <https://www.gnu.org/licenses/>.
 * ******************************************************************************/

const path = require('path');
const version = require('./package.json').version;
const webpack = require('webpack');

const rules = [
    { test: /\.css$/, use: ['style-loader', 'css-loader']}
]

// Note that unfortunately, we cannot declare "vue" an external. JupyterVue
// bundles all of Vue but does not export all of it again for us. (Not sure if
// that would even be possible.) So we have to include our own copy.
// (Otherwise, RequireJS would try to load vue from extensions/vue.js which
// does not exist.

module.exports = (env, argv) => {
    const devtool = argv.mode === 'development' ? 'source-map' : false;
    return [
        {// Notebook extension
        //
        // This bundle only contains the part of the JavaScript that is run on
        // load of the notebook. This section generally only performs
        // some configuration for requirejs, and provides the legacy
        // "load_ipython_extension" function which is required for any notebook
        // extension.
        //
            entry: './src/extension.js',
            output: {
                filename: 'extension.js',
                path: path.resolve(__dirname, '..', 'ipymuvue', 'nbextension'),
                libraryTarget: 'amd',
                publicPath: '' // publicPath is set in extension.js
            },
            devtool,
            externals: [],
            plugins: [],
        },
        {// Bundle for the notebook containing the custom widget views and models
        //
        // This bundle contains the implementation for the custom widget views and
        // custom widget.
        // It must be an amd module
        //
            entry: './src/index.js',
            output: {
                filename: 'index.js',
                path: path.resolve(__dirname, '..', 'ipymuvue', 'nbextension'),
                libraryTarget: 'amd',
                publicPath: '',
            },
            devtool,
            module: {
                rules: rules
            },
            externals: ['@jupyter-widgets/base'],
            plugins: [],
        },
        {// Embeddable ipymuvue bundle
        //
        // This bundle is generally almost identical to the notebook bundle
        // containing the custom widget views and models.
        //
        // The only difference is in the configuration of the webpack public path
        // for the static assets.
        //
        // It will be automatically distributed by unpkg to work with the static
        // widget embedder.
        //
        // The target bundle is always `dist/index.js`, which is the path required
        // by the custom widget embedder.
        //
            entry: './src/index.js',
            output: {
                filename: 'index.js',
                path: path.resolve(__dirname, 'dist'),
                libraryTarget: 'amd',
                publicPath: 'https://unpkg.com/ipymuvue@' + version + '/dist/'
            },
            devtool,
            module: {
                rules: rules
            },
            externals: ['@jupyter-widgets/base'],
            plugins: [],
        }
    ];
}
