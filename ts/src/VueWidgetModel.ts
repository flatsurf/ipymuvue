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
            _model_module_version: `^${version}`,
            _view_module_version: `^${version}`,
            /* the name of the widget, useful for debugging */
            _VueWidget__type: 'VueWidget',
            /* the Vue template to render the widget */
            _VueWidget__template: '<div>…</div>'
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
}
