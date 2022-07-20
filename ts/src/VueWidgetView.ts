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

import { DOMWidgetView } from "@jupyter-widgets/base";
import { VueWidgetModel } from "./VueWidgetModel";
import { createApp, defineComponent, h } from "vue";
import type { App, Component } from "vue";
import type { EventHandler } from "backbone";
import cloneDeep from "lodash-es/cloneDeep";


/*
 * Renders a VueWidget at the client.
 * Namely, this creates a Vue App from the state stored in a VueWidgetModel.
 * It represents the traitlets declared on the VueWidget as reactive Vue `data`
 * and watches it for changes. When a change happens, the model, i.e., the
 * traitlet values, are updated. When a change in the model happens, the Vue
 * `data` is updated.
 */
export class VueWidgetView extends DOMWidgetView {
    // The Vue App rendering this View (there is one app per view)
    private app?: App;

    // The listeners that this view registered on the model. They need to be
    // removed from the model when this view disappears.
    private modelListeners: Array<[string, EventHandler]> = [];

    /*
     * Create a Vue App for this view and display it.
     */
    public override render() {
        super.render();

        (async () => {
          await this.displayed;

          const mountPoint = document.createElement('div');
          this.el.appendChild(mountPoint);

          if (!(this.model instanceof VueWidgetModel))
            throw Error("VueWidgetView can only be created from a VueWidgetModel");

          this.app = createApp(() => h(this.component));
          this.app.mount(mountPoint);
        })();
    }

    /*
     * Destroy the Vue App associated to this view.
     */
    public override remove() {
        this.app?.unmount();

        for (const [event, callback] of this.modelListeners)
          this.model.off(event, callback);

        return super.remove();
    }

    /*
     * Return a Vue component that renders this view.
     */
    private get component() : Component {
      const self = this;
      const model = this.model as VueWidgetModel;

      return defineComponent({
        name: model.get("_VueWidget__type"),
        template: model.get("_VueWidget__template"),
        data() {
          return cloneDeep(model.reactiveState);
        },
        created() {
          for (const key of Object.keys(model.reactiveState))
            self.registerModelListener(`change:${key}`, () => self.onModelChange(key, this));
        },
      });
    }

    /*
     * Register a listener on the model coming from this view that we are going
     * to clean up once the view is destroyed.
     */
    private registerModelListener(event: string, callback: EventHandler) {
      this.model.on(event, callback);
      this.modelListeners.push([event, callback]);
    }

    private onModelChange(attribute: string, component: any) {
      component[attribute] = this.model.get(attribute);
    }
}
