from python_bomberman.server.configuration import ServerConfiguration
import pyglet.app
current_app = None


class App(object):
    def __init__(self, config_file):
        global current_app

        self.config = ServerConfiguration(config_file=config_file)
        current_app = self

    def run(self):
        # let's use pyglet's eventing system for the server's event loop.
        # then we can use pyglet's event system to drive server behaviors as well.
        pyglet.app.EventLoop().run()
