<template>
  <div>Component whose &lt;script&gt; imports a Python module and uses a (<subcomponent-pure-python/>) and a (<subcomponent-with-python-script/>)</div>
</template>
<script>
import { component } from "./component_with_python_script.py";
export default component;
</script>
