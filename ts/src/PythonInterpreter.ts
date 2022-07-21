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

import { JavaScriptLoader } from "./JavaScriptLoader";

export class PythonInterpreter {
  constructor(assets: Record<string, string>) {
    this.assets = assets;
  }

  private readonly assets;

  public async import(name: string): Promise<PyProxy> {
    const pyodide = await this.pyodide;

    return pyodide.pyimport(name);
  }

  public get pyodide(): Promise<PyodideInterface> {
    return (async () => {
      const pyodideModule = await new JavaScriptLoader("pyodide", "https://cdn.jsdelivr.net/pyodide/v0.21.0a3/full/pyodide.js").object;

      const loadPyodideBrowser: typeof loadPyodide = pyodideModule.loadPyodide;
      const pyodide = await loadPyodideBrowser({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.21.0a3/full/"
      });

      for (const [name, content] of Object.entries(this.assets))
        pyodide.FS.writeFile(name, content);

      return pyodide;
    })();
  }

  public asNativeJavaScript(component: Record<string, any>): Record<string, any> {
    component;
    throw Error("not implemented");
  }
}
