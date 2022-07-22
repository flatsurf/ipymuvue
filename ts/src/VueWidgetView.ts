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

import { DOMWidgetView, JupyterPhosphorWidget } from "@jupyter-widgets/base";
import { VueWidgetModel } from "./VueWidgetModel";
import { VueComponentCompiler } from "./VueComponentCompiler";
import { createApp, defineComponent, h } from "vue";
import type { App, Component } from "vue";
import cloneDeep from "lodash-es/cloneDeep";
import mapValues from "lodash-es/mapValues";


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

    /*
     * Create a Vue App for this view and display it.
     */
    public override render() {
        super.render();

        (async () => {
          await this.displayed;

          // TODO: Make tag configurable.
          const mountPoint = document.createElement('div');
          this.el.appendChild(mountPoint);

          if (!(this.model instanceof VueWidgetModel))
            throw Error("VueWidgetView can only be created from a VueWidgetModel");

          const container = await this.container;

          this.app = createApp(() => h(container));
          this.app.mount(mountPoint);
        })();
    }

    /*
     * Destroy the Vue App associated to this view.
     */
    public override remove() {
        this.app?.unmount();

        return super.remove();
    }

    /*
     * Return a Vue component that renders the template defining this view.
     * This is going to be wrapped in the `container` which adds rendering for
     * the slots.
     */
    private get component() : Promise<Component> {
      return (async () => {
        const self = this;
        const model = this.model as VueWidgetModel;
        const components: Record<string, string> = this.model.get("_VueWidget__components");

        return defineComponent({
          name: model.get("_VueWidget__type"),
          template: model.get("_VueWidget__template"),
          data() {
            return cloneDeep(model.reactiveState);
          },
          created() {
            for (const key of Object.keys(model.reactiveState)) {
              // Watch the model: when it changes, update Vue state.
              // Note that the listener is automatically removed when this view is destroyed.
              self.listenTo(self.model, `change:${key}`, () => self.onModelChange(key, this));

              // Watch the Vue state: when it changes, update the model.
              this.$watch(key, () => self.onDataChange(key, this));
            }
          },
          components: await new VueComponentCompiler(
                              this.model.get('_VueWidget__assets')
                            ).compileAsync(components),
          methods: model.methods,
        });
      })();
    }

    /*
     * Return a Vue component that renders this View.
     *
     * We need this additional wrapper to render slots into the component.
     * The wrapper component holds the mapping slot-name -> model-id and
     * creates ``modelRenderer`` components to render into these slots.
     */
    private get container() : Promise<Component> {
      return (async () => {
        const self = this;
        const component = await this.component;
        const modelRenderer = this.modelRenderer;

        return defineComponent({
          name: "VueWidgetContainer",
          data() {
            return {
              // Maps slot name to a widget model id shown in that slot.
              children: {} as Record<string, string>,
            };
          },
          created() {
            const onChange = () => self.onModelChange("_VueWidget__children", this, "children");
            self.listenTo(self.model, "change:_VueWidget__children", onChange);
            onChange();
          },
          render() {
            return h(component, null, mapValues(this.children, (modelId) => {
              return () => h(modelRenderer, {
                modelId: modelId.substring("IPY_MODEL_".length)
              });
            }));
          },
        });
      })();
    }

    /*
     * Return a Vue component that renders a DOMWidgetModel.
     */
    private get modelRenderer() {
      const self = this;

      return defineComponent({
        name: "ModelRenderer",
        props: {
          modelId: String,
        },
        data() {
          return {
            widget: null as { view: DOMWidgetView } | null,
            trash: Object.freeze({ views: [] as DOMWidgetView[] }),
          }
        },
        watch: {
          modelId: {
            /*
             * Create a new DOMWidgetView when the model changes.
             * Schedule the previous view for destruction.
             */
            async handler(current: string, previous: string) {
              if (current === previous)
                return;

              const model = await self.model.widget_manager.get_model(current);

              if (model === undefined) {
                console.error(`ignoring child ${current} which has not active model`);
                return null;
              }

              if (this.widget != null)
                this.trash.views.push(this.widget.view);

              this.widget = Object.freeze({ view: await self.create_child_view(model) });
            },
            immediate: true,
          }
        },
        render() {
          const self = this;
          const widget = this.widget;

          if (widget == null) {
            this.cleanup();
            return;
          }

          return h(defineComponent({
            mounted() {
              JupyterPhosphorWidget.attach((widget.view as DOMWidgetView).pWidget, this.$el);

              self.cleanup();
            },
            render() {
              return h("div");
            }
          }));
        },
        destroyed() {
          this.cleanup();
        },
        methods: {
          cleanup() {
            while (this.trash.views.length)
              this.trash.views.pop()!.remove();
          }
        }
      })
    }

    /*
     * Update Vue's `data` because the widget's model has changed for the
     * `modelAttribute` attribute.
     */
    private onModelChange(modelAttribute: string, component: any, componentAttribute?: string) {
      component[componentAttribute || modelAttribute] = cloneDeep(this.model.get(modelAttribute));
    }

    /*
     * Update the widget's model because Vue's `data` has changed for the `key`
     * attribute.
     */
    private onDataChange(attribute: string, component: any) {
      const value = component[attribute];
      this.model.set(attribute, value === undefined ? null : cloneDeep(value));
      this.model.save_changes();
    }
}
