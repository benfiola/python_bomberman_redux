import python_bomberman.common.map as map
import python_bomberman.common.utils as utils
import pytest


class TestSuite:
    @pytest.fixture
    def map_fixture(self):
        return map.Map(4, 5, name="test")

    @pytest.fixture
    def location(self):
        return utils.Coordinate(2, 2)

    @pytest.fixture
    def player(self, location):
        return map.Player(location)

    def test_init(self, map_fixture):
        assert map_fixture.name == "test"
        assert len(map_fixture.objects) == 4
        assert len(map_fixture.objects[0]) == 5

    def test_add_get_object(self, map_fixture, player):
        map_fixture.add_object(player)
        assert map_fixture.get_object(player.location) == player

    def test_remove_object(self, map_fixture, player):
        self.test_add_get_object(map_fixture, player)
        map_fixture.remove_object(player)
        assert map_fixture.get_object(player.location) is None
