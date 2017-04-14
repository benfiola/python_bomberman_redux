from python_bomberman.client.configuration import ClientConfiguration
from python_bomberman.client.graphics.window import GameWindow
import pyglet.app

# Eh, flask does this for some clever stuff - why can't we?
current_app = None
current_window = None

class App(object):
    def __init__(self, config_file):
        global current_app, current_window

        self.configuration = ClientConfiguration(config_file)
        self.window = GameWindow(
            screen_size=self.configuration.screen_size(),
            fullscreen=self.configuration.fullscreen()
        )

        self._set_globals()

    def _set_globals(self):
        global current_app, current_window
        current_app = self
        current_window = self.window

    def run(self):
        pyglet.app.run()

