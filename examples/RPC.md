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
    display_name: SageMath 9.6
    language: sage
    name: sagemath
---

# Asynchronous RPC with Vue Components
In this example we create an HTML5 `<video>` component on the client, pause and unpause it from the server and query some of its properties.

You could replace `<video>` with any other Vue component or HTML tag and then call its methods from the server.

```sage
from ipymuvue.widgets import VueWidget
from ipymuvue.widgets.asynchronous import run
from traitlets import Unicode

class Video(VueWidget):
    r"""
    Shows 'Elephants Dream' by Orange Open Movie Project Studio, licensed under CC-3.0.
    """
    def __init__(self):
        super().__init__(template=r"""
          <video ref="video" width="512" poster="https://upload.wikimedia.org/wikipedia/commons/e/e8/Elephants_Dream_s5_both.jpg" >
            <source src="https://archive.org/download/ElephantsDream/ed_1024_512kb.mp4" type="video/mp4">
            <source src="https://archive.org/download/ElephantsDream/ed_hd.ogv" type="video/ogg">
            <source src="https://archive.org/download/ElephantsDream/ed_hd.avi" type="video/avi">
            Your browser doesn't support HTML 5 video.
          </video>
        """)
    
    async def play(self):
        r"""
        Start video playback.
        
        Cal&&ls `play` without parameters on the actual video component but does not report its
        return value or any errors.
        """
        await self["video"].play()
        
    async def pause(self):
        r"""
        Pause video playback.
        
        Calls `pause` witout parameters on the actual video component but does not report its
        return value or any errors.      
        """
        await self["video"].pause()
        
    async def paused(self):
        r"""
        Determine whether all the videos are currently paused.
        
        Queries the "paused" attribute of the <video> elements.

        Note that the returned value can safely be awaited despite https://github.com/ipython/ipython/issues/12786
        since we are using https://github.com/Kirill888/jupyter-ui-poll to work around limitations
        in Jupyter's Python kernel.
        """
        return all(
            await self["video"].paused()
        )
    
video = Video()
video
```

Let's show the same video again:

```sage
video
```

Start video playback by calling `.play()` on the `<video>` element.

```sage
await video.play()
```

Pause the video again by calling `.pause()` on the `<video>` elements.

```sage
await video.pause()
```

Query the state of the video asynchronously:

```sage
await video.paused()
```

## Invoking Methods on an Externally Hosted Vue Component

**TODO**: Actually use an external plotly component.

vue-plotly has not been ported to Vue3 yet, so we cannot use it here, currently.

```sage
from ipymuvue.widgets import VueWidget
from traitlets import Unicode

class Plot(VueWidget):
    r"""
    Display a plot with plotly.
    
    Note that in this particular example, it is much easier to just use traitlets
    to synchronize the x and y coordinates.
    The downside of using a traitlet is that it is less efficient since all the
    points need to be transferred to the client with every update.
    """
    def __init__(self):
        super().__init__(template=r"""
            <plotly-plot ref="plotly"/>
        """, components={
            "plotly-plot": r"""
            <template>
                {{ data }}
            </template>
            <script setup>
            import { reactive, defineExpose } from 'vue';
            
            const data = reactive({
                x: [],
                y: [],
                type: 'scatter',
            })
            
            function push(xx, yy) {
                data.x.push(xx);
                data.y.push(yy);
            }
            
            defineExpose({push})
            </script>
            """
        })
    
    async def push(self, x, y):
        r"""
        Add a point with given (x, y) coordinates to the scatter plot.
        """
        await self["plotly"].push(x, y)
    
plot = Plot()
plot
```

```sage
await plot.push(0, 1)
await plot.push(1, 3)
await plot.push(2, 3)
await plot.push(3, 7)
```

## Invoking Async Methods on a Component
In this example, the component on the frontend has a method `wait()` that returns a promise. Invoking this method with `query()` awaits the result of the promise and reports it back to Python.

```sage
from ipymuvue.widgets import VueWidget

class WaitForClick(VueWidget):
    r"""
    Displays a button and waits for the user to click on it.
    """
    def __init__(self):
        super().__init__(template=r"""
        <waiter ref="clickable" />
        """, components={
            "waiter": r"""
            <script>
            export default {
                template: `<button @click='click'>{{ state }}</button>`,
                data() {
                    return {
                        resolve: null
                    };
                },
                computed: {
                    state() {
                        return this.resolve ? 'Waiting for Click.' : 'Ready.';
                    }
                },
                methods: {
                    async wait() {
                        return await new Promise((resolve) => {
                            this.resolve = resolve;
                        })
                    },
                    click() {
                        if (this.resolve)
                            this.resolve('Ok.')
                        this.resolve = null;
                    }
                }
            }
            """})
    
    async def wait(self):
        r"""
        Call the component's `wait` method and await the "Ok." it returns.
        """
        return await self["clickable"].wait(return_when="FIRST_COMPLETED")
    
waiter = WaitForClick()
waiter
```

```sage
waiter
```

```sage
await waiter.wait()
```

## Using Cancellation Tokens

There is a small issue in the above component. Since the same widget is shown twice, we only want the user to click the button in either of the two. But currently, one button is still waiting to be pressed even though nobody is actually waiting for that click anymore. We can of course explicitly ask all the frontend instances to cancel the request:

```sage
from ipymuvue.widgets import VueWidget

class WaitForClick(VueWidget):
    r"""
    Displays a button and waits for the user to click on it.
    """
    def __init__(self):
        super().__init__(template=r"""
        <waiter ref="clickable" />
        """, components={
            "waiter": r"""
            <script>
            export default {
                template: `<button @click='click'>{{ state }}</button>`,
                data() {
                    return {
                        resolve: null
                    };
                },
                computed: {
                    state() {
                        return this.resolve ? 'Waiting for Click.' : 'Ready.';
                    }
                },
                methods: {
                    async wait() {
                        return await new Promise((resolve) => {
                            this.resolve = resolve;
                        })
                    },
                    cancel() {
                        this.resolve = null;
                    },
                    click() {
                        if (this.resolve)
                            this.resolve('Ok.')
                        this.resolve = null;
                    }
                }
            }
            """})
    
    async def wait(self):
        r"""
        Call the component's `wait` method and await the "Ok." it returns.
        """
        value = await self["clickable"].wait(return_when="FIRST_COMPLETED")
        await self["clickable"].cancel()
        return value
    
waiter = WaitForClick()
waiter
```

```sage
waiter
```

```sage
await waiter.wait()
```

However, since this is a very common issue, such cancellation can also be handled directly on the client by providing a `cancel()` method on the returned promise:

```sage
from ipymuvue.widgets import VueWidget

class WaitForClick(VueWidget):
    r"""
    Displays a button and waits for the user to click on it.
    """
    def __init__(self):
        super().__init__(template=r"""
        <waiter ref="clickable" />
        """, components={
            "waiter": r"""
            <script>
            export default {
                template: `<button @click='click'>{{ state }}</button>`,
                data() {
                    return {
                        resolve: null
                    };
                },
                computed: {
                    state() {
                        return this.resolve ? 'Waiting for Click.' : 'Ready.';
                    }
                },
                methods: {
                    wait() {
                        const token = {
                            cancelled: false,
                        };
                        const promise = this.waitAsync(token);
                        promise.cancel = () => {
                            token.cancelled = true;
                            this.cancel();
                        };
                        return promise;
                    },
                    async waitAsync() {
                        return await new Promise((resolve) => {
                            this.resolve = resolve;
                        })
                    },
                    cancel() {
                        this.resolve = null;
                    },
                    click() {
                        if (this.resolve)
                            this.resolve('Ok.')
                        this.resolve = null;
                    }
                }
            }
            """})
    
    async def wait(self):
        r"""
        Call the component's `wait` method and await the "Ok." it returns.
        """
        return await self["clickable"].wait(return_when="FIRST_COMPLETED")
    
waiter = WaitForClick()
waiter
```

```sage
waiter
```

```sage
await waiter.wait()
```

### Calling a Specific View

We repeat the above example but now we call for a specific button to be pressed by setting the `views` parameter.

```sage
from ipymuvue.widgets import VueWidget

class WaitForClick(VueWidget):
    r"""
    Displays a button and waits for the user to click on it.
    """
    def __init__(self):
        super().__init__(template=r"""
        <waiter ref="clickable" />
        """, components={
            "waiter": r"""
            <script>
            export default {
                template: `<button @click='click'>{{ state }}</button>`,
                data() {
                    return {
                        resolve: null
                    };
                },
                computed: {
                    state() {
                        return this.resolve ? 'Waiting for Click.' : 'Ready.';
                    }
                },
                methods: {
                    wait() {
                        const token = {
                            cancelled: false,
                        };
                        const promise = this.waitAsync(token);
                        promise.cancel = () => {
                            token.cancelled = true;
                            this.cancel();
                        };
                        return promise;
                    },
                    async waitAsync() {
                        return await new Promise((resolve) => {
                            this.resolve = resolve;
                        })
                    },
                    cancel() {
                        this.resolve = null;
                    },
                    click() {
                        if (this.resolve)
                            this.resolve('Ok.')
                        this.resolve = null;
                    }
                }
            }
            """})
        
        self._views = None
    
    async def wait(self):
        r"""
        Call the component's `wait` method and await the "Ok." it returns.
        """
        (_, view) = await self["clickable"].wait(return_when="FIRST_COMPLETED", views=self._views, identify=True)
        self._views = view
        return
    
waiter = WaitForClick()
waiter
```

```sage
waiter
```

```sage
await waiter.wait()
```

Now ask the user to click the same button again:

```sage
await waiter.wait()
```

## Error Handling

JavaScript errors are displayed by the Widget:

```sage
from ipymuvue.widgets import VueWidget

class HelloWorld(VueWidget):
    r"""
    Displays a message.
    """
    def __init__(self):
        super().__init__(template=r"""
            <child ref="child" />
        """, components={
            "child": r"""
            <script>
            export default {
                template: `<div>Hello {{ name }}!</div>`,
                data() {
                    return {
                        name: 'noname',
                    };
                },
                methods: {
                    greet: function(name) {
                        if (typeof name !== 'string')
                            throw Error(`name must be a string but was ${name}`)
                        this.name = name;
                        return name;
                    },
                    greetAsync: async function(name) {
                        await new Promise((resolve) => setTimeout(resolve, 1000));
                        return this.greet(name);
                    },
                }
            }
            </script>
            """
        })
    
hello = HelloWorld()
hello
```

```sage
hello
```

```sage
await hello["child"].greet()
```

Extra parameters are ignored by JavaScript, so this is not an error:

```sage
await hello["child"].greet("firstname", "lastname")
```

Missing functions are reported:

```sage
await hello["child"].meet("firstname", "lastname")
```

Exceptions thrown in promises are reported:

```sage
await hello["child"].greetAsync()
```
