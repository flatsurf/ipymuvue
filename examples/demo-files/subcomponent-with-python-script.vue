<template>
  <span class="styled">Subcomponent whose &lt;script&gt; imports a Python module</span>
</template>
<script>
import { component } from "./subcomponent_with_python_script.py";
export default component;
</script>
<style scoped>
.styled {
  color: green;
}
</style>
