from python_bomberman.common.testutils import temp_file
import python_bomberman.server.configuration as configuration
import pytest


class TestSuite:
    @pytest.fixture
    def server_config(self, temp_file):
        return configuration.ServerConfiguration(
            config_file=temp_file
        )

    @pytest.fixture
    def defaults(self):
        return configuration.ServerConfiguration.DEFAULTS

    def test_get_port(self, server_config, defaults):
        assert server_config.port() == defaults[server_config.PORT]

    def test_set_port(self, server_config, defaults):
        old_value = defaults[server_config.PORT]
        new_value = old_value - 1
        server_config.port(new_value)
        assert server_config.port() != old_value
        assert server_config.port() == new_value
