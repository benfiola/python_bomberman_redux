from python_bomberman.common.configuration import Configuration


class ClientConfiguration(Configuration):
    SCREEN_SIZE = "screen_size"
    FULLSCREEN = "fullscreen"
    DEFAULTS = {
        SCREEN_SIZE: (800, 600),
        FULLSCREEN: False
    }

    def __init__(self, config_file):
        super().__init__(
            root="client",
            defaults=self.DEFAULTS,
            config_file=config_file
        )

    def screen_size(self, value=None):
        if not value:
            return self.get(self.SCREEN_SIZE)
        self.set(self.SCREEN_SIZE, value)

    def fullscreen(self, value=None):
        if not value:
            return self.get(self.FULLSCREEN)
        self.set(self.FULLSCREEN, value)
