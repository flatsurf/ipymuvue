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
import { loadModule } from 'vue3-sfc-loader';
import type { Options, Resource, AbstractPath } from 'vue3-sfc-loader';
import { PythonInterpreter } from './PythonInterpreter';
import * as Vue from "vue";

export class VueComponentCompiler {
  public constructor(components: Record<string, string>, assets: Record<string, string>) {
    this.definitions = components;
    this.assets = assets;
  }

  private readonly definitions;
  private readonly assets;

  public get components(): Promise<Record<string, Component>> {
    return (async () => {
      return Object.fromEntries(
        await Promise.all(Object.entries(this.definitions).map(
          async ([name, definition]) => [name, await this.compile(definition)])));
    })();
  }

  private async compile(definition: string) {
    const self = this;

    const options: Options = {
      moduleCache: {
        vue: Vue,
      },
      getFile: async (url) => {
        const path = url.toString();
        if (path in this.assets)
          return this.assets[path]
        throw Error(`cannot resolve ${path} from provided assets`);
      },
      addStyle(textContent) {
        // We currently do not deduplicate styles. We should probably do that,
        // in particular when we get hot-reloading.
        const style = Object.assign(document.createElement('style'), {textContent});
        document.head.appendChild(style);
      },
      async handleModule(type, _getContentData, path_) {
        switch (type) {
          case '.py':
            const interpreter = new PythonInterpreter(self.assets);

            const path = path_.toString();
            if (!path.endsWith(".py"))
              throw Error("Python file must end in .py")

            const name = path.replace(/\//g, '.').substring(0, path.length - 3);

            const module = await interpreter.import(name);
            // const jsModule = interpreter.asNativeJavaScript(module);
            return module;
          default:
            // Work around a typing errors in vue3-sfc-loader.
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

    return await loadModule(definition, options);
  }
}
