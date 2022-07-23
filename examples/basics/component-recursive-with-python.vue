<template>
  <span>
    a recursive component containing
    <span v-if="depth"><component-recursive-with-python :depth="depth - 1"/></span>
    <span v-else>nothing</span>
  </span>
</template>
<script>
import { component } from "./component_recursive_in_python.py";

export default component;
</script>
<style scoped>
span {
  font-size: calc((v-bind(depth) + 1) * .5px);
  opacity: calc((v-bind(depth) * 5% + 10%));
}
</style>
