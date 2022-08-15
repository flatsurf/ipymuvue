<template>
  <pan-zoom-viewport v-if="current" class="pan-zoom" v-slot="{ viewport }">
    <plot :png="current.png" :bounds="current.bounds" :viewport="viewport" @refresh="refresh" />
  </pan-zoom-viewport>
</template>
<script setup>
import { PanZoomViewport } from "https://raw.githubusercontent.com/saraedum/vue-geometry/dist/dist/vue-geometry.mjs";
import Plot from "./Plot.vue";
import { defineProps, defineEmits } from "vue";

defineProps(["current"])

const emit = defineEmits(["redraw"])

function refresh(...args) {
  emit("refresh", ...args);
}
</script>
<style scoped>
.pan-zoom {
  cursor: grab;
}
</style>
