from python_bomberman.server.configuration import ServerConfiguration

current_app = None


class App(object):
    def __init__(self, config_file):
        global current_app

        self.config = ServerConfiguration(config_file=config_file)
        current_app = self
