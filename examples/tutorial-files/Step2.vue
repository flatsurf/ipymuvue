<script setup>
import { reactive, ref } from 'vue'

const counter = reactive({ count: 0 })
const message = ref('Hello World!')
</script>

<template>
  <h4>{{ message }}</h4>
  <p>Count is: {{ counter.count }}</p>
</template>
