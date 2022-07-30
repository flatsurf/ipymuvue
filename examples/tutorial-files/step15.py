from ipymuvue.pyodide.vue import define_component


def create_component(confetti):
    confetti = confetti.new()

    def setup(props, context):
        def show_confetti():
            confetti.addConfetti()

        show_confetti()

        return locals()

    return define_component(
        setup=setup,
        template=r"""
        <h1 @click="show_confetti()">🎉 Congratulations!</h1>
    """,
    )
