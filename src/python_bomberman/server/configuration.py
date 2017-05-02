from python_bomberman.common.configuration import Configuration

class ServerConfiguration(Configuration):
    PORT = "port"
    DEFAULTS = {
        PORT: 12000
    }

    def __init__(self, config_file):
        super().__init__(
            root="server",
            defaults=self.DEFAULTS,
            config_file=config_file
        )

    def port(self, value=None):
        if not value:
            return self.get(self.PORT)
        self.set(self.PORT, value)
