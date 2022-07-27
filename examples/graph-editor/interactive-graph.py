from vue import define_component, ref, watch

def setup(props, context):
    def vertex_rclick(vertex):
        context.emit('vertex-rclick', vertex)

    pos = ref(props.positions)

    def update_positions(new, old, _):
        nonlocal pos
        pos.value = new

    watch(lambda: props.positions, update_positions)

    dragged = ref(None)

    def rclick():
        context.emit('rclick')

    def startdrag(vertex):
        nonlocal dragged
        dragged.value = vertex

    def stopdrag():
        nonlocal dragged
        # Emit should remove reactive wrappers. Somehow this goes wrong
        # without the [0], [1] here. We send an empty {} corresponding to a
        # proxy dict somehow. We don't also seem to be able to send
        # list(.values()) instead. See #12.
        context.emit('dragged', dragged.value, pos.value[dragged.value][0], pos.value[dragged.value][1])
        dragged.value = None

    def drag(event):
        if dragged.value is not None:
            pos.value[dragged.value] = [event.offsetX, event.offsetY]

    return locals()


component = define_component(
    setup=setup,
    props=["vertices", "edges", "positions", "width", "height"],
    emits=["vertex-rclick", "rclick", "dragged"],
    template=r"""
        <svg :width="width" :height="height" @click.right.prevent="rclick()" @mousemove="drag">
            <line v-for="(edge, i) of edges" :key="i" stroke="black" stroke-width="2px"
                :x1="pos[edge[0]][0]" :y1="pos[edge[0]][1]"
                :x2="pos[edge[1]][0]" :y2="pos[edge[1]][1]"
            />
            <g v-for="vertex of vertices" :key="vertex"
                style="cursor: pointer"
                @mousedown.left="startdrag(vertex)"
                @mouseup.left="stopdrag()"
                @click.right.prevent.stop="vertex_rclick(vertex)">
                <circle r="6"
                    fill="cornflowerblue"
                    stroke="red"
                    :stroke-width="(dragged == vertex) ? 10 : 0"
                    :cx="pos[vertex][0]"
                    :cy="pos[vertex][1]"/>
                <circle r="18" fill="transparent"
                    :cx="pos[vertex][0]"
                    :cy="pos[vertex][1]"/>
            </g>
        </svg>
    """)
