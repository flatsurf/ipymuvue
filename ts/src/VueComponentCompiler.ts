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

import type { Component } from "vue";
import { defineAsyncComponent } from "vue";
import { loadModule } from 'vue3-sfc-loader';
import type { Options, Resource, AbstractPath } from 'vue3-sfc-loader';
import { PythonInterpreter } from './PythonInterpreter';
import * as Vue from "vue";
import isCallable from "is-callable";

export class VueComponentCompiler {
  public constructor(assets?: (name: string) => DataView | null);
  public constructor(assets?: Record<string, DataView>);
  public constructor(assets?: Record<string, DataView> | ((name: string) => DataView | null)) {
    this.assets = assets || {};
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

          return {
            getContentData: async (binary: Boolean) => {
              const asset = isCallable(this.assets) ?
                this.assets(path) :
                this.assets[path];
              if (asset) {
                if (!(asset.buffer instanceof ArrayBuffer))
                  throw Error(`asset of incorrect type: ${asset}`)

                return binary ? asset.buffer : new TextDecoder().decode(asset.buffer);
              }

              if (path.startsWith("https://")) {
                const raw = await fetch(path);
                return await raw.text();
              }

              throw Error(`cannot resolve ${path} from provided assets`);
            },
            type: path.includes('.') ? ("." + path.split('.').pop()!) : "",
          }
        },
        addStyle(textContent) {
          // We currently do not deduplicate styles. We should probably do that,
          // in particular when we get hot-reloading.
          const style = Object.assign(document.createElement('style'), {textContent});
          document.head.appendChild(style);
        },
        handleModule: async(type, getContentData, path_) => {
          const path = path_.toString();

          switch (type) {
            case '.py':
              const content = await getContentData(true);
              if (typeof content === "string")
                throw Error("getContentData(true) should have returned binary data but found a literal string instead");
              await this.pyodide.provisionAssets({[path]: new DataView(content)});
              if (!(this.assets instanceof Function))
                await this.pyodide.provisionAssets(this.assets);
              (await this.pyodide.pyodide).registerJsModule("ipymuvue_vue_component_compiler", { VueComponentCompiler })

              if (!path.endsWith(".py"))
                throw Error("Python file must end in .py")

              const name = path.replace(/\//g, '.').substring(0, path.length - 3);

              const pyodide = await this.pyodide.pyodide;
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

      const module = await loadModule(filename, options);

      if (filename.toLowerCase().endsWith(".py"))
        return (module as any).component;
      return module;
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
