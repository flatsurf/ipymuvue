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

import type { PyodideInterface } from "pyodide";

type FS = PyodideInterface["FS"];

export class AssetProvisioner {
  constructor(FS: FS) {
    this.FS = FS;
  }

  private readonly FS;

  public async provision(name: string, content: DataView) {
      if (name.lastIndexOf('/') != -1)
        await this.mkdir(name.substring(0, name.lastIndexOf('/')));

      const stat = this.FS.analyzePath(name, true);

      const provisioned = {
        replaced: false,
        abspath: stat.path,
      };

      if (stat.exists) {
        if (AssetProvisioner.equal(this.FS.readFile(name), content.buffer))
          return provisioned;

        provisioned.replaced = true;
      }

      this.FS.writeFile(name, new Uint8Array(content.buffer), { encoding: "binary" });

      return provisioned;
  }

  /*
   * Create directory `name` recursively.
   */
  private async mkdir(name: string) {
    if (name.lastIndexOf('/') != -1)
      await this.mkdir(name.substring(0, name.lastIndexOf('/')));

    if (!this.FS.analyzePath(name, true).exists)
      await this.FS.mkdir(name);
  }

  private static equal(lhs: ArrayBuffer, rhs: ArrayBuffer) {
    if (lhs.byteLength !== rhs.byteLength)
      return false;

    const a = new Uint8Array(lhs);
    const b = new Uint8Array(rhs);

    return a.every((x, i) => x === b[i]);
  }
}
