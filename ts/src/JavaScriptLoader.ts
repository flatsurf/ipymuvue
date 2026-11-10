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
  constructor(url: string, integrity?: string) {
    this.url = url;
    this.integrity = integrity;
  }

  private readonly url;
  private readonly integrity;

  /*
   * Load the script with a <script> tag and return the global object that the
   * script populated.
   *
   * Note that we do not load scripts through RequireJS even if it is
   * present, e.g., when widgets are embedded in static HTML, since the
   * scripts we load (pyodide.js) are not AMD modules.
   */
  public get object(): Promise<any> {
    return this.loadBrowser();
  }

  private async loadBrowser() {
    const script = document.createElement("script");
    const load = new Promise<void>((resolve, reject) => {
      script.addEventListener("load", () => resolve());
      script.addEventListener("error", () => reject());
    });

    script.async = true;
    script.src = this.url;
    if (this.integrity) script.integrity = this.integrity;
    script.crossOrigin = "anonymous";

    document.head.appendChild(script);
    await load;

    return window;
  }
}
