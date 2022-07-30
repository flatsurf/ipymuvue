<script setup>
import JSConfetti from 'https://unpkg.com/js-confetti@0.10.2/dist/js-confetti.min.js'

const confetti = new JSConfetti()

function showConfetti() {
  confetti.addConfetti()
}

showConfetti()
</script>

<template>
  <h1 @click="showConfetti">🎉 Congratulations!</h1>
</template>

<style scoped>
h1 {
  text-align: center;
  cursor: pointer;
}
</style>
