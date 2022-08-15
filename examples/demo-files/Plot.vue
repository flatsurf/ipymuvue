<template>
  <img draggable="false" :src="src" :style="`transform: ${transform}; will-change: transform;`" />
</template>
<script setup>
import { computed, watch } from "vue";
import { Viewport } from "https://raw.githubusercontent.com/saraedum/vue-geometry/dist/dist/vue-geometry.mjs";
import Flatten from "https://unpkg.com/@flatten-js/core@1.3.5/dist/main.umd.js";

const props = defineProps(["viewport", "png", "bounds"]);
const emit = defineEmits(["refresh"])

const width = 602;
const height = 384;

let generation = 0;

const { clientCoordinateSystem, idealCoordinateSystem } = Viewport.use(props.viewport);

idealCoordinateSystem.defineEmbedding(clientCoordinateSystem, new Flatten.Matrix(width, 0, 0, -height, 0, height));

const src = computed(() => {
  return `data:image/png;charset=utf-8;base64,${props.png}`;
})

const transform = computed(() => {
  const visibleBox = clientCoordinateSystem.box(0, 0, width, height);
  const providedBox = clientCoordinateSystem.embed(
    idealCoordinateSystem.box(props.bounds.xmin, props.bounds.ymin, props.bounds.xmax, props.bounds.ymax)
  );

  const scaleX = providedBox.width / visibleBox.width;
  const scaleY = providedBox.height / visibleBox.height;

  return `matrix(${scaleX}, 0, 0, ${scaleY}, ${providedBox.low.x - (1 - scaleX) / 2 * visibleBox.width}, ${providedBox.low.y - (1 - scaleY) / 2 * visibleBox.height})`;
});

let wanted = computed(() => {
  return idealCoordinateSystem.embed(
    clientCoordinateSystem.box(0, 0, width, height)
  );
})

watch(() => wanted.value, (c, p) => {
  if (c.equal_to(p))
    return;

  const current = ++generation;
  setTimeout(() => {
    if (current === generation) {
      emit("refresh", {
        xmin: wanted.value.low.x,
        ymin: wanted.value.low.y,
        xmax: wanted.value.high.x,
        ymax: wanted.value.high.y,
      })
    }
  }, 50);
})
</script>
<style scoped>
img {
  user-select: none;
}
</style>
