from ipymuvue.pyodide.vue import define_component, ref, watch, vue_compatible


def create_setup(gsap):
    def setup(props, context):
        def vertex_rclick(vertex):
            context.emit("vertex-rclick", vertex)

        pos = ref(props.positions)

        def update_positions(new, old, _):
            nonlocal pos
            pos.value = {
                vertex: pos.value.get(vertex, new.get(vertex)) for vertex in new
            }
            for vertex in new:
                gsap.to(
                    vue_compatible(pos.value[vertex]),
                    vue_compatible(
                        {
                            "duration": 0.5,
                            "0": new[vertex][0],
                            "1": new[vertex][1],
                        },
                        reference=False,
                    ),
                )

        watch(lambda: props.positions, update_positions)

        dragged = ref(None)

        def rclick():
            context.emit("rclick")

        def startdrag(vertex):
            nonlocal dragged
            dragged.value = vertex

        def stopdrag():
            nonlocal dragged
            dragged.value = None

        def drag(event):
            if dragged.value is not None:
                pos.value[dragged.value] = [event.offsetX, event.offsetY]

        return locals()

    return setup


def create_component(gsap):
    return define_component(
        setup=create_setup(gsap),
        props=["vertices", "edges", "positions", "width", "height"],
        emits=["vertex-rclick", "rclick"],
    )
