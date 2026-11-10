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

import type {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
} from "@jupyterlab/application";
import { IJupyterWidgetRegistry } from "@jupyter-widgets/base";
import { VueWidgetModel, VueWidgetView, version } from "./index";

/*
 * The JupyterLab plugin that registers our widgets with ipywidgets.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: "ipymuvue:plugin",
  requires: [IJupyterWidgetRegistry],
  activate: (_app: JupyterFrontEnd, registry: IJupyterWidgetRegistry) => {
    registry.registerWidget({
      name: "ipymuvue",
      version,
      exports: { VueWidgetModel, VueWidgetView },
    });
  },
  autoStart: true,
};

export default plugin;
