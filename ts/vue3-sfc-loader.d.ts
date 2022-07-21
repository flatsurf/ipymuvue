// Work around https://github.com/FranckFreiburger/vue3-sfc-loader/pull/134
declare module 'vue3-sfc-loader' {
  import { loadModule, AbstractPath, Resource, PathContext, ModuleHandler, Options, ContentData, File } from "vue3-sfc-loader/dist/types/vue3-esm"
  export { loadModule, AbstractPath, Resource, PathContext, ModuleHandler, Options, ContentData, File };
}
