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

export class JavaScriptLoader {
  constructor(name: string, url: string, integrity?: string) {
    this.name = name;
    this.url = url;
    this.integrity = integrity;
  }

  private readonly name;
  private readonly url;
  private readonly integrity;

  public get object(): Promise<any> {
    return (async () => {
      const globals = window as any;
      if (typeof globals.requirejs == 'function') {
        return await this.loadRequireJS(globals.requirejs);
      } else {
        return await this.loadBrowser();
      }
    })();
  }

  private async loadRequireJS(requirejs: any) {
    if (!this.url.endsWith('.js'))
      throw Error("url must end with .js to be loaded through RequireJS");
    requirejs.config({
      paths: {
        [this.name]: this.url.substring(0, this.url.length - 3)
      },
      onNodeCreated: function(node: HTMLScriptElement, _config: any, moduleName: string, _url: string) {
        if (moduleName === this.name) {
          if (this.integrity)
            node.integrity = this.integrity;
          node.crossOrigin = "anonymous";
        }
      },
    });
    return await new Promise((resolve, reject) => {
      requirejs([this.name], function(module: any) {
        resolve(module);
      }, function(err: any) {
        reject(err);
      });
    });
  }

  private async loadBrowser() {
    const script = document.createElement("script");
    const load = new Promise<void>((resolve, reject) => {
      script.addEventListener("load", () => resolve());
      script.addEventListener("error", () => reject());
    });

    script.async = true;
    script.src = this.url;
    if (this.integrity)
      script.integrity = this.integrity;
    script.crossOrigin = "anonymous";

    document.head.appendChild(script);
    await load;

    return window;
  }
}
