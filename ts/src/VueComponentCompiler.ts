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

import type { Component } from "vue";
import { defineAsyncComponent } from "vue";
import { loadModule } from 'vue3-sfc-loader';
import type { Options, Resource, AbstractPath } from 'vue3-sfc-loader';
import { PythonInterpreter } from './PythonInterpreter';
import * as Vue from "vue";

export class VueComponentCompiler {
  public constructor(assets: Record<string, DataView>) {
    this.assets = assets;
    this.pyodide = new PythonInterpreter();
  }

  private readonly assets;
  private readonly pyodide;

  public compile(filename: string): Component {
    return defineAsyncComponent(() => this.compileAsync(filename));
  }

  public async compileAsync(filename: string): Promise<Component>;
  public async compileAsync(components: Record<string, string>): Promise<Record<string, Component>>;
  public async compileAsync(filename: string | Record<string, string>) {
    if (typeof filename === "string") {
      const options: Options = {
        moduleCache: {
          vue: Vue,
        },
        getFile: async (path_) => {
          const path = path_.toString();

          if (path in this.assets) {
            return {
              getContentData: async (binary: Boolean) => {
                const asset = this.assets[path];

                if (!(asset.buffer instanceof ArrayBuffer))
                  throw Error(`asset of incorrect type: ${asset}`)

                return binary ? asset.buffer : new TextDecoder().decode(asset.buffer);
              },
              type: path.includes('.') ? ("." + path.split('.').pop()!) : "",
            };
          }

          throw Error(`cannot resolve ${path} from provided assets`);
        },
        addStyle(textContent) {
          // We currently do not deduplicate styles. We should probably do that,
          // in particular when we get hot-reloading.
          const style = Object.assign(document.createElement('style'), {textContent});
          document.head.appendChild(style);
        },
        handleModule: async(type, _getContentData, path_) => {
          const path = path_.toString();

          switch (type) {
            case '.py':
              // TODO: These are probably not the correct assets to provision.
              // Since this instance gets called through the
              // VUE_COMPONENT_COMPILER hack, this.assets might not have updated?
              // See also the comment in vue.py.
              await this.pyodide.provisionAssets(this.assets);

              if (!path.endsWith(".py"))
                throw Error("Python file must end in .py")

              const name = path.replace(/\//g, '.').substring(0, path.length - 3);

              const pyodide = await this.pyodide.pyodide;
              const vue = pyodide.pyimport("vue");
              vue.__VUE_COMPONENT_COMPILER__(this)

              return pyodide.pyimport(name);
            default:
              // Work around a typing error in vue3-sfc-loader.
              return undefined as unknown as null;
          }
        },
        getResource(_path, _options_): Resource {
          throw Error("not implemented");
        },
        pathResolve(_path): AbstractPath {
          throw Error("not implemented");
        },
      };

      // Work around typing errors in vue3-sfc-loader.
      delete((options as any).getResource);
      delete((options as any).pathResolve);

      return await loadModule(filename, options);
    } else {
      const components = filename;
      return (async () => {
        return Object.fromEntries(
          await Promise.all(Object.entries(components).map(
            async ([name, filename]) => {
              return [name, await this.compileAsync(filename)]
            })));
      })();
    }
  }
}
