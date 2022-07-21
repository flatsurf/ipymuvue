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

import type { PyodideInterface } from "pyodide";

type FS = PyodideInterface["FS"];

export class AssetProvisioner {
  constructor(FS: FS) {
    this.FS = FS;
  }

  private readonly FS;

  public async provision(name: string, content: DataView) {
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

  private static equal(lhs: ArrayBuffer, rhs: ArrayBuffer) {
    if (lhs.byteLength !== rhs.byteLength)
      return false;

    const a = new Uint8Array(lhs);
    const b = new Uint8Array(rhs);

    return a.every((x, i) => x === b[i]);
  }
}
