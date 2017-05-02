from python_bomberman.common.testutils import temp_file
import python_bomberman.common.configuration as configuration
import pytest
import os
import json


class TestSuite:
    @pytest.fixture
    def rooted_config(self, temp_file):
        return configuration.Configuration(
            defaults={"test_key": "test_value"},
            config_file=temp_file,
            root="test"
        )

    @pytest.fixture
    def non_rooted_config(self, temp_file):
        return configuration.Configuration(
            defaults={"test_key": "test_value"},
            config_file=temp_file
        )

    @pytest.fixture
    def reconcile_dict(self):
        return {
            "to_be_reconciled": "to_be_reconciled_value",
            "test": {
                "to_be_reconciled": "to_be_reconciled_value"
            }
        }

    @pytest.fixture
    def reconciled_rooted_config(self, temp_file, reconcile_dict):
        with open(temp_file, 'w') as f:
            f.write(json.dumps(reconcile_dict))
        return self.rooted_config(temp_file)

    @pytest.fixture
    def reconciled_non_rooted_config(self, temp_file, reconcile_dict):
        with open(temp_file, 'w') as f:
            f.write(json.dumps(reconcile_dict))
        return self.non_rooted_config(temp_file)

    def _test_init(self, config):
        assert config is not None
        assert os.path.isfile(config.config_file) is True

    def _test_get(self, config):
        assert config.get("test_key") == "test_value"
        with pytest.raises(configuration.ConfigurationException):
            config.get("not_in_config")

    def _test_set(self, config):
        config.set("test_key", "test_value_changed")
        assert config.get("test_key") == "test_value_changed"
        with pytest.raises(configuration.ConfigurationException):
            config.set("not_in_config", "not_in_config_value")

    def _test_reconciliation(self, config):
        assert config.get("test_key") == "test_value"
        with pytest.raises(configuration.ConfigurationException):
            config.get("to_be_pruned")

    def test_init_no_root(self, non_rooted_config):
        self._test_init(non_rooted_config)

    def test_init_root(self, rooted_config):
        self._test_init(rooted_config)

    def test_get_no_root(self, non_rooted_config):
        self._test_get(non_rooted_config)

    def test_get_root(self, rooted_config):
        self._test_get(rooted_config)

    def test_set_no_root(self, non_rooted_config):
        self._test_set(non_rooted_config)

    def test_set_root(self, rooted_config):
        self._test_set(rooted_config)

    def test_reconciliation_root(self, reconciled_rooted_config):
        self._test_reconciliation(reconciled_rooted_config)

    def test_reconciliation_no_root(self, reconciled_non_rooted_config):
        self._test_reconciliation(reconciled_non_rooted_config)

