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
    const options = {
      moduleCache: {
        vue: Vue,
      },
      getFile: async (url: string) => {
        if (url in this.assets)
          return this.assets[url]
        throw Error(`cannot resolve ${url} from provided assets`);
      },
      addStyle(textContent: string) {
        // We currently do not deduplicate styles. We should probably do that,
        // in particular when we get hot-reloading.
        const style = Object.assign(document.createElement('style'), {textContent});
        document.head.appendChild(style);
      },
    }
    // Note that the typings of vue3-sfc-loader are incorrect so we need to
    // cast to any to convince it to not require us to implement getResource().
    return await loadModule(definition, options as any);
  }
}
