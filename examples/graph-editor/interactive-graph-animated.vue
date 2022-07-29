<template>
  <svg :width="width" :height="height" @click.right.prevent.stop="rclick()" @mousemove="drag">
      <line v-for="(edge, i) of edges" :key="i" stroke="black" stroke-width="2px"
          :x1="pos[edge[0]][0]" :y1="pos[edge[0]][1]"
          :x2="pos[edge[1]][0]" :y2="pos[edge[1]][1]"
      />
      <g v-for="vertex of vertices" :key="vertex"
          style="cursor: pointer"
          @mousedown="startdrag(vertex)"
          @mouseup="stopdrag()"
          @click.right.prevent.stop="vertex_rclick(vertex)">
          <circle r="6"
              fill="cornflowerblue"
              stroke="red"
              :stroke-width="(dragged == vertex) ? 10 : 0"
              :cx="pos[vertex][0]"
              :cy="pos[vertex][1]"/>
          <circle r="18" fill="transparent"
              :cx="pos[vertex][0]"
              :cy="pos[vertex][1]"/>
      </g>
  </svg>
</template>
<script>
import { create_component } from "./interactive-graph-animated.py";
import gsap from "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.2.4/gsap.min.js";

const component = create_component(gsap)

export default component;
</script>
