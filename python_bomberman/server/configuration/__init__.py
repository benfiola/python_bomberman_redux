from python_bomberman.common.configuration import Configuration

class ServerConfiguration(Configuration):
    DEFAULTS = {
        "port": 12000
    }

    def __init__(self, config_file):
        super().__init__(
            root="server",
            defaults=self.DEFAULTS,
            config_file=config_file
        )