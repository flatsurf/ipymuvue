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

// Currently, the pyodide package only works from Node but not in the browser.
// We load the full pyodide distribution from their CDN servers and only use
// the typings of the pyodide NPM package.
import type { loadPyodide, PyodideInterface, PyProxy } from "pyodide";
import { AssetProvisioner } from "./Assets";

import { JavaScriptLoader } from "./JavaScriptLoader";

/*
 * A Python interpreter powered by pyodide.
 *
 * Unfortunately, the interpreter is a singleton since pyodide does not support
 * multiple Python instances yet, see
 * https://pyodide.org/en/0.19.1/usage/api/js-api.html#globalThis.loadPyodide
 */
export class PythonInterpreter {
  private static instance: Promise<PyodideInterface> | null = null;

  /*
   * Absolute paths of all the files provisioned.
   */
  private static provisioned = new Set<string>();

  /*
   * Create the named assets in the emscription file system.
   *
   * If any loaded Python modules are contained in the assets, reload them.
   */
  public async provisionAssets(assets: Record<string, DataView>) {
    const pyodide = await this.pyodide;

    const modules = await this.modules;
    const provisioner = new AssetProvisioner(pyodide.FS);

    let reload = false;
    
    for (const [name, content] of Object.entries(assets)) {
      const provisioned = await provisioner.provision(name, content)

      PythonInterpreter.provisioned.add(provisioned.abspath);

      if (provisioned.replaced) {
        console.info(`replaced modified asset ${name}`);

        if (provisioned.abspath in modules) {
          console.log(`will reload all modules because loaded module ${name} changed`);
          reload = true;
        }
      }
    }

    if (reload)
      for (const module of Object.values(modules))
        if (PythonInterpreter.provisioned.has(module.__file__)) {
          console.debug(`reloading ${module}`);
          pyodide.pyimport("importlib").reload(module);
        }
  }

  private get modules(): Promise<Record<string, PyProxy>> {
    return (async () => {
      const modules: Record<string, PyProxy> = {};

      const sys = (await this.pyodide).pyimport('sys');
      for (const module of sys.modules.values())
        if ("__file__" in module)
          modules[module.__file__ as string] = module;

      return modules;
    })();
  }

  public get pyodide(): Promise<PyodideInterface> {
    if (PythonInterpreter.instance == null)
      PythonInterpreter.instance = (async () => {
        const pyodide = await new JavaScriptLoader("pyodide", "https://cdn.jsdelivr.net/pyodide/v0.21.0a3/full/pyodide.js").object;

        const loadPyodideBrowser: typeof loadPyodide = pyodide.loadPyodide;
        return await loadPyodideBrowser({
          indexURL: "https://cdn.jsdelivr.net/pyodide/v0.21.0a3/full/"
        });
      })();

    return PythonInterpreter.instance;
  }
}
