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

import type { VueWidgetModel } from "./VueWidgetModel";
import { VueWidgetView } from "./VueWidgetView";
import isEmpty from "lodash-es/isEmpty";
import mapValues from "lodash-es/mapValues";
import pickBy from "lodash-es/pickBy";
import type { ComponentPublicInstance } from "vue";
import isPromise from "is-promise";

/*
 * A message sent by the Python backend to tell us to invoke `target` on `path`
 * with `args`.
 */
export type InvocationMessage = {
  // The name of the method or property.
  target: string,
  // The sequence of refs to follow to get to the element defining the `target`.
  path: string[],
  // Arguments to invoke the `target` with.
  args: any[],
  // A unique identifier to report results back to Python.
  identifier: string,
  // Which widgets view to target; all if `null`.
  views: null | string | string[],
  // When to report back to Python.
  return_when: "FIRST_COMPLETED" | "FIRST_EXCEPTION" | "ALL_COMPLETED" | "IGNORE",
};

/*
 * The result of an invocation or an error message if an exception happened.
 */
type InvocationResult<T> = { result: T } | { error: string };

/*
 * A `T` with the name of the view to which it belongs.
 */
type WithView<T> = { view: string } & T;

/*
 * The holder of methods or properties to invoke in a view.
 */
type InvocationTarget = ComponentPublicInstance | HTMLElement;


/*
 * Performs invocations of methods on all views of a `model`.
 */
export class Handler {
  public constructor(model: VueWidgetModel, message: InvocationMessage) {
    this.model = model;
    this.message = message;
  }

  private readonly model;
  private readonly message;

  /*
   * A mapping
   *   view name -> view
   * for all views representing this model.
   */
  private get views(): Promise<{[view: string]: VueWidgetView}> {
    return (async () => {
      const views = mapValues(await Handler.unwrapPromisedValues(this.model.views),
        (view) => {
          if (!(view instanceof VueWidgetView))
            throw Error("views of a VueWidgetModel must all be VueWidgetView");
          return view;
        });

      // Target all views if targets has not been set.
      if (this.message.views == null) {
        return views;
      }

      if (typeof(this.message.views) === "string") {
        if (!(this.message.views in views))
          throw Error(`no view ${this.message.views} found`)
        return {[this.message.views]: views[this.message.views]};
      }

      return Object.fromEntries(this.message.views.map((view) => {
        if (!(view in views))
          throw Error(`no view ${this.message.views} found`)
        return [view, views[view]];
      }));
    })();
  }

  /*
   * Return the component obtained by following the `path` of refs specified in
   * a `InvocationMessage` on the `view`.
   */
  private resolveElement(view: VueWidgetView): InvocationTarget | undefined {
    if (this.message.path.length === 0)
      throw Error("path for invocation must not be empty");

    let target: InvocationTarget | undefined = view.vnode;

    if (target === undefined) {
      console.warn("cannot access into $refs of view which is not mounted; ignoring view");
      return;
    }

    for (const fragment of this.message.path) {
      if (!("$refs" in target))
        throw Error("not a Vue component, cannot access its $refs");

      target = target.$refs[fragment] as InvocationTarget | undefined;

      if (target === undefined) {
        console.warn(`component has no (mounted) ref ${fragment}; ignoring view`);
        return;
      }
    }

    return target;
  }

  /*
   * A mapping 
   *   view name -> component defining method to invoke
   * for all views representing this model.
   */
  private get elements(): Promise<{[view: string]: InvocationTarget}> {
    return (async () => {
      const targets = await Handler.unwrapPromisedValues(mapValues(await this.views, (view) => this.resolveElement(view)));

      // Ignore views that do not define the target.
      return pickBy(targets, (target) => target != null) as any;
    })();
  }

  /*
   * Turn a {key: Promise<T>} into a Promise<{key: T}>.
   */
  private static async unwrapPromisedValues<T = {[key:string]: Promise<any>}>(object: T): Promise<{[key in keyof T]: Awaited<T[key]>}> {
    const entries = Object.entries(object).map(
      async ([key, promise]) => [key, await promise]);
    return Object.fromEntries(await Promise.all(entries));
  }

  /*
   * Report a result back to Python as the verdict of this invocation.
   */
  private report<T>(results: WithView<InvocationResult<T>>[]) {
    const message = {
      identifier: this.message.identifier,
      results,
    }

    this.model.send(message, {});
  }

  /*
   * Return a promise holding the result of invocation of the target method on
   * a single view.
   */
  private invoke(target: InvocationTarget) {
    try {
      let value = (target as any)[this.message.target];

      if (value === undefined)
        throw Error(`no method or property ${this.message.target} exposed on target`);

      if (value instanceof Function) {
        value = value.bind ? value.bind(target) : value;
        value = value(...this.message.args);
      } else if (this.message.args.length) {
        throw Error(`cannot call ${this.message.target} with arguments since it is not a function`);
      }

      let cancel = () => {};

      if (isPromise(value)) {
        if ("cancel" in value)
            cancel = value["cancel"];
      } else {
        value = Promise.resolve(value);
      }

      return {
        result: (async () => {
          try {
            return { result: await value };
          } catch (e) {
            console.info(e);
            return { error: Handler.renderError(e) };
          }
        })(),
        cancel,
      };
    } catch (e) {
      console.info(e);

      return {
        result: Promise.resolve({
          error: Handler.renderError(e),
        }),
        cancel: () => {},
      }
    }
  }

  private static renderError(e: any) {
    return e instanceof Error ? e.message : JSON.stringify(e);
  }

  /*
   * Invoke the `target` specified in the `message` with `args` on each view
   * and report the result.
   */
  public async run() {
    try {
      const elements = await this.elements;

      if (isEmpty(elements)) {
        if (this.message.return_when === "FIRST_COMPLETED")
          throw Error("no (mounted) targets found for this invocation");

        this.report([]);
        return;
      }

      // Create a mapping view -> { result, cancel }
      // where `cancel` is a function that tries to abort the invocation and
      // `result` is morally just a promise that resolves to the result of the
      // invocation.
      // However, `result` actually resolves to the result of the computation
      // and the name of the view again so we can easily implement the
      // different return_when strategies below.
      const invocations =
        mapValues(elements, (target, view) => {
          const {result, cancel} = this.invoke(target);
          return {
            result: (async () => ({
              ...await result,
              view,
            }))(),
            cancel,
          };
        });

      switch(this.message.return_when) {
        case "IGNORE":
          return;
        case "ALL_COMPLETED":
        {
          const promisedResults = Object.values(invocations).map((result) => result.result);
          const results = await Promise.all(promisedResults);
          this.report(results);
          return;
        }
        case "FIRST_COMPLETED":
        {
          const promisedResults = Object.values(invocations).map((result) => result.result);
          const first = await Promise.race(promisedResults);
          this.report([first]);
          delete invocations[first.view];
          mapValues(invocations, (invocation) => invocation.cancel());
          return;
        }
        case "FIRST_EXCEPTION":
        {
          const results = [];

          while (!isEmpty(invocations)) {
            const promisedResults = Object.values(invocations).map((result) => result.result);
            const first = await Promise.race(promisedResults);
            delete invocations[first.view];

            if ("error" in first) {
              this.report([first]);
              mapValues(invocations, (invocation) => invocation.cancel());
              return;
            }

            results.push(first);
          }

          this.report(results);
          return;
        }
        default:
          throw Error(`not implemented: cannot handle return_when ${this.message.return_when} yet`);
      }
    } catch (e) {
      console.info(e);

      this.report([
        { error: Handler.renderError(e), view: "unknown" },
      ]);
    }
  }
}
