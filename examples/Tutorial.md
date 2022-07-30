---
jupyter:
  jupytext:
    formats: ipynb,md
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.0
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# Basics of Vue.js in ipyμvue

We go through some very basic features of Vue.js, namely the ones that are shown in the official [↗ tutorial](https://vuejs.org/tutorial/). Unless you are already familiar with Vue.js, you should really **work through that compact tutorial first** or at the same time since we are not explaining any of these concepts here.

In this document, we verify that all these concepts work in widgets written with ipyμvue. And we also showcase, the different ways that widgets can be written. Namely

* Leaving the state in the Python instance on the server using **traitlets**. In this setup all event handlers run on the server and all state is constantly synchronized with the client, i.e., the web browser. This is probably the easiest way to write a widget, however there are limitations. The constant back and forth between server and client adds a lot of overhead and certain real-time interactions might not be possible. Also, the traitlet model is not entirely compatible with the Vue.js model. Namely, state stored in traitlets is only synchronized when the state is completely replaced. Modifications to nested state are not seen by the other side. If you are familiar with Vue.js, you can think of traitlets as shallow refs.

* Minimal glue in Python and implementation of the Vue components in `.vue` **single file components**. This should work well for many use cases. The only drawback is that one has to use plain JavaScript for the components and cannot use TypeScript (however, note that your code is being run through babel so you can use all JavaScript features and they should get transpiled.)

* Minimal glue in Python on the server and Vue components in `.py` files interpreted by **pyodide**. This option is **highly experimental**. Also, it comes with some performance penalties. Python is much slower than JavaScript at the moment and at the interface between Python and Vue.js some transformations are necessary that might be costly in some cases.

* Minimal glue in Python and components from an **external package**. For larger projects, this would probably be the best approach. You can use all the build tools, hot-module reloading, … while developing a Vue.js library and then consume it in a widget. This approach is not shown here, an example of consuming an external package is in the [Demo]([./Demo.md) notebook. For a full example of a widget following this approach, have a look at [ipyvue-flatsurf](https://github.com/flatsurf/ipyvue-flatsurf) which consumes the [vue-flatsurf](https://flatsurf/vue-flatsurf) components.

```python
def show_source(fname):
    r"""
    Show source code of the external file ``fname``.
    
    Used below to display ``assets`` that are used in the components with proper syntax highlighting.
    """
    from IPython.display import Markdown
    display(Markdown(f"```{fname.split('.')[-1]}\n{open(fname).read()}```"))
```

## (1) Getting Started / (2) Declarative Rendering

See [↗ Getting Started](https://vuejs.org/tutorial/#step-1) and [↗ Declarative Rendering](https://vuejs.org/tutorial/#step-1) for the corresponding sections of the Vue tutorial.

We can load single file components, they can be directly provided as a string.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-2 />
        """, components={
            "step-2": r"""
                <script setup>
                import { reactive, ref } from 'vue'

                const counter = reactive({ count: 0 })
                const message = ref('Hello World!')
                </script>

                <template>
                    <h4>{{ message }}</h4>
                    <p>Count is: {{ counter.count }}</p>
                </template>
            """
        })
        
Widget()
```

Or we can load a single file component from a file which gives you better support in your favorite editor.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-2 />
        """, components={
            "step-2": open("tutorial-files/Step2.vue")
        })
        
Widget()
```

```python
show_source('tutorial-files/Step2.vue')
```

The same frontend code can also be implemented in Python, though this is quite experimental and if you don't mind JavaScript, it's probably better to stick with the classic approach.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-2 />
        """, components={
            "step-2": open("tutorial-files/step2.py")
        })
        
Widget()
```

```python
show_source("tutorial-files/step2.py")
```

We can also implement this server-side by synchronizing the state between frontend and backend. Note that `{"counter": 0}` is not deeply reactive in this case. Changes to `counter` are not picked up by the frontend since the state only is synchronized when the entire `{}` object is rewritten.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Dict, Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <h4>{{ message }}</h4>
            <p>Count is: {{ counter.count }}</p>
        """)
    
    message = Unicode("Hello World!").tag(sync=True)
    counter = Dict({"count": 0}).tag(sync=True)
    
Widget()
```

## (3) Attribute Bindings

See [↗ Attribute Binding](https://vuejs.org/tutorial/#step-3) for the corresponding section of the Vue tutorial.

As usual, we can use the value of a variable in a template by prepending a `:`.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-3/>
        """, components={"step-3": r"""
            <script setup>
            import { ref } from 'vue'

            const titleClass = ref('title')
            </script>

            <template>
              <h4 :class="titleClass">Make me red</h4>
            </template>

            <style>
            .title {
              color: red;
            }
            </style>
        """})
        
Widget()
```

We could also move the component implementation to a separate `.vue` file and `open()` that file instead of including the string literally.


We can currently not implement this in the exact same way entirely in Python since we cannot declare a `<style>` block in Python. However, we can use a `.vue` component whose `<script>` is essentially implemented in Python (**experimental**.)

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-3/>
        """, components={"step-3": r"""
            <script>
            import { component } from "./step3.py";
            export default component;
            </script>
            <style>
            .title {
              color: red;
            }
            </style>
        """}, assets={
            "step3.py": open("tutorial-files/step3.py"),
        })

Widget()
```

```python
show_source("tutorial-files/step3.py")
```

Again we could keep the state synchronized between server and client and use a traitlet here but we'd have to use an extra `.vue` component to emit our (non-scoped) `<style>` block.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <h4 :class="titleClass">Make me red</h4>
        """, components={
            "widget-style": r"""
                <style>
                .title {
                  color: red;
                }
                </style>
            """
        })
        
    titleClass = Unicode("title").tag(sync=True)
        
Widget()
```

## (4) Event Listeners

See [↗ Event Listeners](https://vuejs.org/tutorial/#step-4) for the corresponding section of the Vue tutorial.


Event listeners are bound with the usual `@` syntax.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
                <step-4/>
        """, components={
            "step-4": r"""
                <script setup>
                import { ref } from 'vue'

                const count = ref(0)

                function increment() {
                  count.value++
                }
                </script>

                <template>
                  <button @click="increment">count is: {{ count }}</button>
                </template>
            """,
        })
        
Widget()
```

We could also move the component implementation to a separate `.vue` file and `open()` that file instead of including the string literally.


Event handlers can also be defined as Python functions in the frontend (**experimental**.)

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-4/>
        """, components={
            "step-4": open("tutorial-files/step4.py")
        })
        
Widget()
```

```python
show_source('tutorial-files/step4.py')
```

We can also keep the event handler here in the notebook code, by marking it as `@VueWidget.callback`.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Int

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <button @click="increment">count is: {{ count }}</button>
        """)
        
    count = Int(0).tag(sync=True)
    
    @VueWidget.callback
    def increment(self, event):
        self.count += 1
    
Widget()
```

## (5) Form Bindings

See [↗ Form Bindings](https://vuejs.org/tutorial/#step-5) for the corresponding section of the Vue tutorial.


A form can be bound to a variable by listening to changes explicitly.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-5/>
        """, components={
            "step-5": r"""
            <script setup>
            import { ref } from 'vue'

            const text = ref('')

            function onInput(e) {
              text.value = e.target.value
            }
            </script>

            <template>
              <input :value="text" @input="onInput" placeholder="Type here">
              <p>{{ text }}</p>
            </template>
        """})
        
Widget()
```

We get the same affect using `v-model`.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-5/>
        """, components={
            "step-5": r"""
            <script setup>
            import { ref } from 'vue'

            const text = ref('')
            </script>

            <template>
              <input v-model="text" placeholder="Type here">
              <p>{{ text }}</p>
            </template>
        """})
        
Widget()
```

We could also move the component implementation to a separate `.vue` file and `open()` that file instead of including the string literally.


This also works with components implemented in Python (**experimental**).

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-5/>
        """, components={
            "step-5": open("tutorial-files/step5.py")
        })
        
Widget()
```

```python
show_source('tutorial-files/step5.py')
```

We can also bind a traitlet with `v-model`.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <input v-model="text" placeholder="Type here">
            <p>{{ text }}</p>
        """)
        
    text = Unicode().tag(sync=True)
    
Widget()
```

## (6) Conditional Rendering

See [↗ Conditional Rendering](https://vuejs.org/tutorial/#step-6) for the corresponding section of the Vue tutorial.

We get conditional rendering with `v-if` and `v-else`.

There is no difficulty for the implementation here, so we only showcase this with a traitlets backend.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Bool

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <button @click="toggle">toggle</button>
            <h4 v-if="awesome">Vue is awesome!</h4>
            <h4 v-else>Oh no 😢</h4>
        """)
        
    awesome = Bool(True).tag(sync=True)
    
    @VueWidget.callback
    def toggle(self, event):
        self.awesome = not self.awesome
        
Widget()
```

## (7) List Rendering

See [List Rendering](https://vuejs.org/tutorial/#step-7) for the corresponding section of the Vue tutorial.

We iterate over a list of items with `v-for`.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-7/>
        """, components={
            "step-7": r"""
            <script setup>
            import { ref } from 'vue'

            // give each todo a unique id
            let id = 0

            const newTodo = ref('')
            const todos = ref([
              { id: id++, text: 'Learn HTML' },
              { id: id++, text: 'Learn JavaScript' },
              { id: id++, text: 'Learn Vue' }
            ])

            function addTodo() {
              todos.value.push({ id: id++, text: newTodo.value })
              newTodo.value = ''
            }

            function removeTodo(todo) {
              todos.value = todos.value.filter((t) => t !== todo)
            }
            </script>

            <template>
              <form @submit.prevent="addTodo">
                <input v-model="newTodo">
                <button>Add Todo</button>
              </form>
              <ul>
                <li v-for="todo in todos" :key="todo.id">
                  {{ todo.text }}
                  <button @click="removeTodo(todo)">X</button>
                </li>
              </ul>
            </template>
        """})
        
Widget()
```

The component can be implemented in an external `.vue` component.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-7/>
        """, components={
            "step-7": open("tutorial-files/Step7.vue")
        })

Widget()
```

```python
show_source('tutorial-files/Step7.vue')
```

The component can also be implemented in Python on the client (**experimental**.)

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-7/>
        """, components={
            "step-7": open("tutorial-files/step7.py")
        })

Widget()
```

```python
show_source("tutorial-files/step7.py")
```

We can also implement everything server-side, with traitlets backing:

```python
from ipymuvue.widgets import VueWidget
from traitlets import List, Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
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
        """)
        
        self.todos = [
            {"id": Widget.next_id(), "text": "Learn HTML"},
            {"id": Widget.next_id(), "text": "Learn Python"},
            {"id": Widget.next_id(), "text": "Learn Vue"},            
        ]
        
    id = 0
    
    @staticmethod
    def next_id():
        Widget.id += 1
        return Widget.id
        
    new_todo = Unicode().tag(sync=True)
    todos = List().tag(sync=True)
    
    @VueWidget.callback
    def add_todo(self, event):
        # Cannot use .append() here since traitlets only synchronize when they are rewritten completely.
        self.todos = self.todos + [{"id": Widget.next_id(), "text": self.new_todo}]
        
    @VueWidget.callback
    def remove_todo(self, todo):
        self.todos = [item for item in self.todos if item != todo]
    
Widget()
```

## (8) Computed Properties

See [↗ Computed Properties](https://vuejs.org/tutorial/#step-8) for the corresponding section of the Vue tutorial.

Dependent computed properties can be declared as `computed`.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-8/>
        """, components={"step-8": r"""
            <script setup>
            import { ref, computed } from 'vue'

            let id = 0

            const newTodo = ref('')
            const hideCompleted = ref(false)
            const todos = ref([
              { id: id++, text: 'Learn HTML', done: true },
              { id: id++, text: 'Learn JavaScript', done: true },
              { id: id++, text: 'Learn Vue', done: false }
            ])

            const filteredTodos = computed(() => {
              return hideCompleted.value
                ? todos.value.filter((t) => !t.done)
                : todos.value
            })

            function addTodo() {
              todos.value.push({ id: id++, text: newTodo.value, done: false })
              newTodo.value = ''
            }

            function removeTodo(todo) {
              todos.value = todos.value.filter((t) => t !== todo)
            }
            </script>

            <template>
              <form @submit.prevent="addTodo">
                <input v-model="newTodo" />
                <button>Add Todo</button>
              </form>
              <ul>
                <li v-for="todo in filteredTodos" :key="todo.id">
                  <input type="checkbox" v-model="todo.done">
                  <span :class="{ done: todo.done }">{{ todo.text }}</span>
                  <button @click="removeTodo(todo)">X</button>
                </li>
              </ul>
              <button @click="hideCompleted = !hideCompleted">
                {{ hideCompleted ? 'Show all' : 'Hide completed' }}
              </button>
            </template>

            <style>
            .done {
              text-decoration: line-through;
            }
            </style>
        """})
                         
Widget()
```

We could also move the component implementation to a separate `.vue` file and `open()` that file instead of including the string literally.


If we move the styling to a separate component, we can implement this entirely in Python on the frontend (**experimental**.)

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-8/>
        """, components={
            "step-8": open("tutorial-files/step8.py"),
            "widget-style": r"""
            .done {
              text-decoration: line-through;
            }
            """})
                         
Widget()
```

```python
show_source('tutorial-files/step8.py')
```

We can not really obtain the same effect with traitlets on the server since there is (afaik) no such thing as `computed` for traitlets. We could register an event listener with `.on` of course.


## (9) Lifecycle and Template Refs

See [↗ Lifecycle and Template Refs](https://vuejs.org/tutorial/#step-9) for the corresponding section of the Vue tutorial.

We can listen to lifecycle events such as `onMounted` and reference components in our template directly with `ref`.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-9/>
        """, components={"step-9": r"""
            <script setup>
            import { ref, onMounted } from 'vue'

            const p = ref(null)

            onMounted(() => {
              p.value.textContent = 'mounted!'
            })
            </script>

            <template>
              <p ref="p">hello</p>
            </template>
        """})
                         
Widget()
```

We could also move the component implementation to a separate `.vue` file and `open()` that file instead of including the string literally.


We can implement this entirely in Python on the frontend (**experimental**.)

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-9/>
        """, components={
            "step-9": open("tutorial-files/step9.py")
        })
                         
Widget()
```

```python
show_source('tutorial-files/step9.py')
```

Lifecycle events are currently not exposed on widgets that are purely implemented with traitlets. Neither is `ref`, see [#1](https://github.com/flatsurf/ipymuvue/issues/1).


## (10) Watchers

See [↗ Watchers](https://vuejs.org/tutorial/#step-10) for the corresponding section of the Vue tutorial.

We can `watch` reactive state for changes.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-10/>
        """, components={
            "step-10": r"""
                <script setup>
                import { ref, watch } from 'vue'

                const todoId = ref(1)
                const todoData = ref(null)

                async function fetchData() {
                  todoData.value = null
                  const res = await fetch(
                    `https://jsonplaceholder.typicode.com/todos/${todoId.value}`
                  )
                  todoData.value = await res.json()
                }

                fetchData()

                watch(todoId, fetchData)
                </script>

                <template>
                  <p>Todo id: {{ todoId }}</p>
                  <button @click="todoId++">Fetch next todo</button>
                  <p v-if="!todoData">Loading...</p>
                  <pre v-else>{{ todoData }}</pre>
                </template>
            """
        })
        
Widget()
```

We could also move the component implementation to a separate `.vue` file and `open()` that file instead of including the string literally.


We can implement this entirely in Python on the frontend (**experimental**.)

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-10/>
        """, components={
            "step-10": open("tutorial-files/step10.py")
        })
                         
Widget()
```

```python
show_source('tutorial-files/step10.py')
```

When implementing the state of a component with traitlets, we can use the usual `.observe` to listen for changes. Note that `watch()` in Vue is not a deep watcher, so there is no fundamental difference between the two here. Note also that unlike with a `@VueWidget.callback`, output and exceptions that happen in the handler are not displayed.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Int, Dict

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
          <p>Todo id: {{ todo_id }}</p>
          <button @click="todo_id++">Fetch next todo</button>
          <p v-if="!todo_data">Loading...</p>
          <pre v-else>{{ todo_data }}</pre>
        """)
        
        self.fetch_data()
        self.observe(lambda _: self.fetch_data(), "todo_id")

    todo_id = Int(1).tag(sync=True)
    todo_data = Dict(None, allow_none=True).tag(sync=True)

    def fetch_data(self):
        self.todo_data = None
        
        async def _fetch_data():
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://jsonplaceholder.typicode.com/todos/{self.todo_id}") as response:
                    self.todo_data = await response.json()
                    
        import asyncio
        asyncio.create_task(_fetch_data())
        
Widget()
```

## (11) Components

See [↗ Components](https://vuejs.org/tutorial/#step-11) for the corresponding section of the Vue tutorial.


Subcomponents of a `VueWidget` can be registered in the `components` dict.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <ChildComp />
        """, components={
            "ChildComp": r"""
            <template>
              <h4>A Child Component!</h4>
            </template>
            """
        })
        
Widget()
```

This does not make the component available to child components, they need to export the component as part of their setup. To be able to `import` a `.vue` component in a child, it needs to be provided as an asset.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-11 />
        """, components={
            "step-11": r"""
            <template>
                <ChildComp />
            </template>
            <script setup>
            import ChildComp from "ChildComp.vue";
            </script>
            """
        }, assets={
            "ChildComp.vue": open('tutorial-files/ChildComp11.vue')
        })
        
Widget()
```

```python
show_source("tutorial-files/ChildComp11.vue")
```

A component that is purely implemented in Python (**experimental**) can not exactly follow this pattern. We can use the `components` field of the *Options API* and read the component from a file (which is a different syntax than what Vue.js normally does.)

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-11 />
        """, components={
            "step-11": open("tutorial-files/step11.py")
        }, assets={
            "ChildComp.vue": open("tutorial-files/ChildComp11.vue"),
        })
        
Widget()
```

```python
show_source('tutorial-files/step11.py')
```

## (12) Props

See [↗ Props](https://vuejs.org/tutorial/#step-12) for the corresponding section of the Vue tutorial.


When using `<script setup>` in a `.vue` file, props can be declared with `defineProps()`.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <ChildComp :msg="greeting"/>
        """, components={
            "ChildComp": open("tutorial-files/ChildComp12.vue")
        })
        
    greeting = Unicode("Hello from parent").tag(sync=True)


Widget()
```

```python
show_source("tutorial-files/ChildComp12.vue")
```

A component that is purely implemented in Python (**experimental**) uses the `props` parameter to declare its props.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <ChildComp :msg="greeting"/>
        """, components={
            "ChildComp": open("tutorial-files/step12.py")
        })
        
    greeting = Unicode("Hello from parent").tag(sync=True)


Widget()
```

```python
show_source("tutorial-files/step12.py")
```

Note that traitlets are not implemented as props on the component. They are reactive state that can also be written to.

We do not support a `VueWidget` to be a subcomponent of a component, so there is no feature corresponding to props in components backed by traitlets. Note that `VueWidget` can be used inside components using slots (below.)


## (13) Emits

See [↗ Emits](https://vuejs.org/tutorial/#step-13) for the corresponding section of the Vue tutorial.


We can emit custom events with `emit()` in the composition API and listen to them in the parent component with a `@`.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <ChildComp @response="(msg) => child_msg = msg" />
            <p>{{ child_msg }}</p>
        """, components={
            "ChildComp": open("tutorial-files/ChildComp13.vue")
        })

    child_msg = Unicode("No child msg yet").tag(sync=True)
        
Widget()
```

```python
show_source('tutorial-files/ChildComp13.vue')
```

In a Python component (**experimental**) we have to `emit` on the context since the `defineEmits()` macro is not available.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <ChildComp @response="(msg) => child_msg = msg" />
            <p>{{ child_msg }}</p>
        """, components={
            "ChildComp": open("tutorial-files/step13.py")
        })

    child_msg = Unicode("No child msg yet").tag(sync=True)
        
Widget()
```

## (14) Slots

See [↗ Slots](https://vuejs.org/tutorial/#step-14) for the corresponding section of the Vue tutorial.


Template fragments can be rendered in `<slot>` outlets.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <ChildComp>
                Message: {{ msg }}
            </ChildComp>
        """, components={
            "ChildComp": r"""
            <template>
                <slot>Fallback content</slot>
            </template>
            """
        })
        
    msg = Unicode("from parent").tag(sync=True)
        
Widget()
```

This works exactly the same for components written entirely in Python.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <ChildComp>
                Message: {{ msg }}
            </ChildComp>
        """, components={
            "ChildComp": open("tutorial-files/step14.py")
        })
        
    msg = Unicode("from parent").tag(sync=True)
        
Widget()
```

```python
show_source("tutorial-files/step14.py")
```

Note that we are not limited to showing Vue components in slots. Arbitrary widgets can be passed on to slots.

```python
from ipymuvue.widgets import VueWidget
from traitlets import Unicode
from ipywidgets import Textarea

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <ChildComp>
                <slot>No child widget assigned to slot.</slot>
            </ChildComp>
        """, components={
            "ChildComp": r"""
            <template>
                <slot>Fallback content</slot>
            </template>
            """
        })
        
        self.slot(Textarea())
        
Widget()
```

## (15) You Did It!

See [↗ You Did It!](https://vuejs.org/tutorial/#step-15) for the corresponding section of the Vue tutorial.


We can load external packages at runtime. Note the <span style="color:red">security implications</span>: such external JavaScript code (as any JavaScript code that other widgets use) could in principle send arbitrary commands to the running kernel, i.e., it could run arbitrary commands on your host machine. By using such external resources, you are entrusting the system to the external package author and the CDN from which you are downloading the package. The latter can be fixed by providing the package bundled with your widget and provisioning it as an asset.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-15 />
        """, components={
            "step-15": open("tutorial-files/Step15.vue")
        })
        
Widget()
```

```python
show_source("tutorial-files/Step15.vue")
```

We cannot use an external package in a component that is entirely written in Python (**experimental**.) Instead, we need a tiny bit of glue code in a `.vue` file. Also, we cannot emit a `<style>` block without that file.

```python
from ipymuvue.widgets import VueWidget

class Widget(VueWidget):
    def __init__(self):
        super().__init__(template=r"""
            <step-15 />
        """, components={
            "step-15": r"""
            <script>
            import JSConfetti from 'https://unpkg.com/js-confetti@0.10.2/dist/js-confetti.min.js'
            import { create_component } from "./step15.py";
            const component = create_component(JSConfetti)
            export default component;
            </script>
            <style scoped>
            h1 {
                text-align: center;
                cursor: pointer;
            }
            </style>
            """
        }, assets={
            "step15.py": open("tutorial-files/step15.py")  
        })
        
Widget()
```

```python
show_source("tutorial-files/step15.py")
```
