from ipymuvue.pyodide.vue import define_component, ref


def setup(props, context):
    id = 0

    def next_id():
        nonlocal id
        id += 1
        return id

    new_todo = ref("")
    todos = ref(
        [
            {"id": next_id(), "text": "Learn HTML"},
            {"id": next_id(), "text": "Learn Python"},
            {"id": next_id(), "text": "Learn Vue"},
        ]
    )

    def add_todo(event):
        todos.value.append({"id": next_id(), "text": new_todo})

    def remove_todo(todo):
        todos.value = [item for item in todos.value if item != todo]

    return locals()


component = define_component(
    setup=setup,
    template=r"""
  <form @submit.prevent="add_todo">
    <input v-model="new_todo">
    <button>Add Todo</button>
  </form>
  <ul>
    <li v-for="todo in todos" :key="todo.id">
      {{ todo.text }}
      <button @click="remove_todo(todo)">X</button>
    </li>
  </ul>
""",
)
