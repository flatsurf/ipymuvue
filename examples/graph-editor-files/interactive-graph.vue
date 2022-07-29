<template>
  <svg :width="width" :height="height" @click.right.prevent.stop="relayout()" @mousemove="drag">
      <line v-for="(edge, i) of edges" :key="i" stroke="black" stroke-width="2px"
          :x1="pos[edge[0]][0]" :y1="pos[edge[0]][1]"
          :x2="pos[edge[1]][0]" :y2="pos[edge[1]][1]"
      />
      <g v-for="vertex of vertices" :key="vertex"
          style="cursor: pointer"
          @mousedown="startdrag(vertex)"
          @mouseup="stopdrag()"
          @click.right.prevent.stop="vertex_rclick(vertex)">
          {{ typeof(pos[vertex]) }}
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
import { defineComponent } from "vue";
import gsap from "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.2.4/gsap.min.js";

export default defineComponent({
  data() {
    return {
      pos: this.positions,
      dragged: null,
    };
  },
  created() {
    this.$watch(() => this.positions, (current) => {
      // this.pos = current;
      this.pos = Object.fromEntries(Object.entries({...current, ...this.pos}).filter(([k, _v]) => k in current));
      Object.keys(current).map(vertex => {
        gsap.to(this.pos[vertex], { duration: .5, "0": current[vertex][0], "1": current[vertex][1]});
      });
    });
  },
  methods: {
    vertex_rclick(vertex) {
      this.$emit('vertex-rclick', vertex);
    },
    relayout() {
        this.$emit('rclick');
    },
    startdrag(vertex) {
        this.dragged = vertex;
    },
    stopdrag() {
        this.dragged = null;
    },
    drag(event) {
      if (this.dragged != null) {
        this.pos[this.dragged] = [event.offsetX, event.offsetY];
      }
    }
  },
  props: ["vertices", "edges", "positions", "width", "height"],
  emits: ["vertex-rclick", "rclick"],
});
</script>
