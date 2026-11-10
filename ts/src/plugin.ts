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

import type { IPlugin } from "@lumino/coreutils";
import { IJupyterWidgetRegistry } from "@jupyter-widgets/base";
import { VueWidgetModel, VueWidgetView, version } from "./index";

/*
 * The JupyterLab plugin that registers our widgets with ipywidgets.
 *
 * We do not use JupyterFrontEndPlugin from @jupyterlab/application here
 * since we do not need the application and @jupyterlab/application pulls
 * in lots of dependencies.
 */
const plugin: IPlugin<unknown, void> = {
  id: "ipymuvue:plugin",
  requires: [IJupyterWidgetRegistry],
  activate: (_app: unknown, registry: IJupyterWidgetRegistry) => {
    registry.registerWidget({
      name: "ipymuvue",
      version,
      exports: { VueWidgetModel, VueWidgetView },
    });
  },
  autoStart: true,
};

export default plugin;
