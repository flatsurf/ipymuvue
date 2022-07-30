from ipymuvue.pyodide.vue import define_component, ref, computed


def setup(props, context):
    id = 0

    new_todo = ref("")

    def next_id():
        nonlocal id
        id += 1
        return id

    hide_completed = ref(False)
    todos = ref(
        [
            {"id": next_id(), "text": "Learn HTML", "done": True},
            {"id": next_id(), "text": "Learn Python", "done": True},
            {"id": next_id(), "text": "Learn Vue", "done": False},
        ]
    )

    @computed
    def filtered_todos():
        if hide_completed.value:
            return [todo for todo in todos.value if not todo["done"]]
        return todos.value

    def add_todo(event):
        todos.value.append({"id": next_id(), "text": new_todo, "done": False})

    def remove_todo(todo):
        todos.value = [item for item in todos.value if item != todo]

    def toggle():
        nonlocal hide_completed
        hide_completed.value = not hide_completed.value

    return locals()


component = define_component(
    setup=setup,
    template=r"""
    <form @submit.prevent="add_todo">
        <input v-model="new_todo" />
        <button>Add Todo</button>
    </form>
    <ul>
        <li v-for="todo in filtered_todos" :key="todo.id">
            <input type="checkbox" v-model="todo.done">
            <span :class="{ done: todo.done }">{{ todo.text }}</span>
            <button @click="remove_todo(todo)">X</button>
        </li>
    </ul>
    <button @click="toggle()">
        {{ hide_completed ? 'Show all' : 'Hide completed' }}
    </button>
""",
)
