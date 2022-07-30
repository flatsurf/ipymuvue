<script setup>
const props = defineProps({
  msg: String
})
</script>

<template>
  <h4>{{ msg || 'No props passed yet' }}</h4>
</template>
