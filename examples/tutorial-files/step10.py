from ipymuvue.pyodide.vue import define_component, ref, watch


def setup(props, context):
    todo_id = ref(1)
    todo_data = ref(None)

    def increment():
        todo_id.value += 1

    # This does not currently work, see #14
    # async def fetch_data(*args):
    #     todo_data.value = None

    #     import pyodide
    #     res = await pyodide.http.pyfetch(f"https://jsonplaceholder.typicode.com/todos/{todo_id.value}")

    #     todo_data.value = await res.json()

    def fetch_data(*_):
        async def _fetch_data():
            todo_data.value = None

            import pyodide

            res = await pyodide.http.pyfetch(
                f"https://jsonplaceholder.typicode.com/todos/{todo_id.value}"
            )

            todo_data.value = await res.json()

        import asyncio

        asyncio.create_task(_fetch_data())

    fetch_data()

    watch(todo_id, fetch_data)

    return locals()


component = define_component(
    setup=setup,
    template=r"""
  <p>Todo id: {{ todo_id }}</p>
  <button @click="increment()">Fetch next todo</button>
  <button @click="fetch_data()">Refetch same todo</button>
  <p v-if="!todo_data">Loading...</p>
  <pre v-else>{{ todo_data }}</pre>
""",
)
