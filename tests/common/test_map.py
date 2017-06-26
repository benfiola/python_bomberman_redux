from python_bomberman.common.testutils import temp_file
import python_bomberman.common.map as map
import python_bomberman.common.utils as utils
import pytest
import os


class TestSuite:
    @pytest.fixture
    def dimensions(self):
        return utils.Coordinate(4, 5)

    @pytest.fixture
    def empty_map(self, dimensions):
        return map.Map(dimensions, name="test")

    @pytest.fixture
    def populated_map(self, empty_map):
        empty_map.add(map.Player(utils.Coordinate(0, 0)))
        empty_map.add(map.Player(utils.Coordinate(3, 4)))
        empty_map.add(map.DestructibleWall(utils.Coordinate(1, 1)))
        empty_map.add(map.IndestructibleWall(utils.Coordinate(2, 2)))
        return empty_map

    @pytest.fixture
    def map_equal(self, populated_map):
        return populated_map

    @pytest.fixture
    def map_unmatching_values(self, populated_map):
        class Bogus:
            def __init__(self):
                self.name = populated_map.name + " nope"
                self.dimensions = utils.Coordinate(populated_map.dimensions.x - 1, populated_map.dimensions.y - 1)
                self.objects = lambda: populated_map[:1]
        return Bogus()

    @pytest.fixture
    def map_missing_attrs(self):
        class Bogus:
            def __init__(self):
                pass
        return Bogus()

    @pytest.fixture
    def map_different_map_objs(self, populated_map):
        class BogusObj:
            identifier = "bogus"

            def __init__(self, location):
                self.location = location

        class Bogus:
            def __init__(self):
                self.name = populated_map.name
                self.dimensions = populated_map.dimensions
                self._objects = populated_map.all_objects()

            def objects(self):
                self._objects[0] = BogusObj(self._objects[0].location)
                return self._objects

        return Bogus()

    @pytest.fixture
    def location(self):
        return utils.Coordinate(2, 2)

    @pytest.fixture
    def player(self, location):
        return map.Player(location)

    def test_init(self, empty_map):
        assert empty_map.name == "test"
        assert empty_map.dimensions

    def test_add_get_object(self, empty_map, player):
        assert len(empty_map.all_objects()) == 0
        empty_map.add(player)
        assert empty_map.object_at_location(player.location) == player
        assert len(empty_map.all_objects()) == 1

    def test_remove_object(self, empty_map, player):
        self.test_add_get_object(empty_map, player)
        empty_map.remove(player)
        assert empty_map.object_at_location(player.location) is None
        assert len(empty_map.all_objects()) == 0

    def test_save_map(self, populated_map, temp_file):
        assert not os.path.exists(temp_file)
        populated_map.save(temp_file)
        assert os.path.isfile(temp_file)

    def test_load_map(self, populated_map, temp_file):
        self.test_save_map(populated_map, temp_file)
        loaded_map = map.Map.load(temp_file)
        assert populated_map == loaded_map

    def test_equal(self, populated_map, map_equal, map_unmatching_values, map_missing_attrs, map_different_map_objs):
        assert populated_map == map_equal
        assert populated_map != map_unmatching_values
        assert populated_map != map_missing_attrs
        assert populated_map != map_different_map_objs
