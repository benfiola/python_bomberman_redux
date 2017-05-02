import pyglet.window


class GameWindow(pyglet.window.Window):
    def __init__(self, screen_size, fullscreen):
        super().__init__(
            width=screen_size[0],
            height=screen_size[1],
            fullscreen=fullscreen
        )

