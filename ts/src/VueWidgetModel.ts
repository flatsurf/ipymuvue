/* ******************************************************************************
 * Copyright (c) 2022 Julian Rüth <julian.rueth@fsfe.org>
 *
 * ipyvue3 is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * ipyvue3 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with ipyvue3. If not, see <https://www.gnu.org/licenses/>.
 * ******************************************************************************/

import { DOMWidgetModel } from "@jupyter-widgets/base";

const version = require('../package.json').version;


export class VueWidgetModel extends DOMWidgetModel {
    defaults() {
        return {
            ...super.defaults(),
            /* standard ipywidgets attributes */
            _model_name: 'VueWidgetModel',
            _view_name: 'VueWidgetView',
            _model_module: 'ipyvue3',
            _view_module: 'ipyvue3',
            _model_module_version: `~${version}`,
            _view_module_version: `~${version}`,
            /* the name of the widget, useful for debugging */
            _VueWidget__type: 'VueWidget',
            /* the Vue template to render the widget */
            _VueWidget__template: '<div>…</div>',
            /* callbacks in Python that are `methods` on the Vue instance */
            _VueWidget__methods: [],
            /* child components that can be used in this component's template */
            _VueWidget__components: {},
            /* files that can be used to define child components */
            _VueWidget__assets: {},
            /* widgets for the (named) slots of the component */
            _VueWidget__children: {},
        };
    }

    /*
     * Return the part of the model that defines its state, excluding bits that
     * are not supposed to change once the model has been created.
     */
    public get reactiveState(): Object {
      const specialAttributes = ['layout', ...Object.keys(this.defaults())];

      return Object.fromEntries(
        this.keys().filter((key) => !specialAttributes.includes(key)).
          map((key) => [key, this.get(key)]));
    }

    /*
     * Return the `methods` callbacks that can be invoked on each Vue app
     * representing this model.
     */
    public get methods() {
      const names = this.get('_VueWidget__methods') as string[];
      return Object.fromEntries(names.map(method =>
        [method, (args?: any[]) => this.callback(method, args || [])]));
    }

    /*
     * Call `method` on the backend with `args`.
     */
    private callback(method: string, args: any[]) {
      this.send({method, args}, this.callbacks());
    }
}
