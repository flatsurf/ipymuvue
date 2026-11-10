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

export * as Vue from "vue";

export { default as cloneDeep } from "lodash-es/cloneDeep"
export { default as clone } from "lodash-es/clone"

export function withArity(f: Function, n: number) {
  if (n === 2) {
    function wrap(n0: any, n1: any) {
      return f(n0, n1);
    }
    return wrap
  }

  throw Error("not implemented")
}

export function asVueCompatibleFunction(f: (...args: any) => any, createPyProxy: (obj: any) => any, vueCompatible: (obj: any) => any) {
  function g(...args: any[]) {
    return vueCompatible(f(...args.map((arg) => createPyProxy(arg))));
  }
  return g
}
