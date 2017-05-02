from python_bomberman.common.testutils import temp_file
import python_bomberman.client.configuration as configuration
import pytest


class TestSuite():
    @pytest.fixture
    def client_config(self, temp_file):
        return configuration.ClientConfiguration(
            config_file=temp_file
        )

    @pytest.fixture
    def defaults(self):
        return configuration.ClientConfiguration.DEFAULTS

    def test_get_screen_size(self, client_config, defaults):
        assert client_config.screen_size() == defaults[client_config.SCREEN_SIZE]

    def test_get_fullscreen(self, client_config, defaults):
        assert client_config.fullscreen() == defaults[client_config.FULLSCREEN]

    def test_set_screen_size(self, client_config, defaults):
        old_value = defaults[client_config.SCREEN_SIZE]
        new_value = (old_value[0] - 1, old_value[1] - 1)
        client_config.screen_size(new_value)
        assert client_config.screen_size() != old_value
        assert client_config.screen_size() == new_value

    def test_set_fullscreen(self, client_config, defaults):
        old_value = defaults[client_config.FULLSCREEN]
        new_value = (not old_value)
        client_config.fullscreen(new_value)
        assert client_config.fullscreen() != old_value
        assert client_config.fullscreen() == new_value
