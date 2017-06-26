import pytest
from python_bomberman.common.game.entity_map import EntityMap
from python_bomberman.common.game.entities import Player
import python_bomberman.common.utils as utils
from python_bomberman.common.game.exceptions import GameException

class TestSuite:
    @pytest.fixture
    def entity_map(self):
        return EntityMap()

    @pytest.fixture
    def player(self):
        return Player(location=utils.Coordinate(0, 0))

    def test_init(self, entity_map):
        assert entity_map._entities is not None

    def test_add(self, entity_map, player):
        assert player.unique_id not in entity_map._entities
        entity_map.add(player)
        assert player.unique_id in entity_map._entities

        # duplicate unique id will throw an exception
        with pytest.raises(GameException):
            entity_map.add(player)

    def test_remove(self, entity_map, player):
        entity_map.add(player)
        assert player.unique_id in entity_map._entities
        entity_map.remove(player)
        assert player.unique_id not in entity_map._entities

        # nonexistent unique id will throw an exception on remove here.
        with pytest.raises(GameException):
            entity_map.remove(player)

    def test_get(self, entity_map, player):
        assert entity_map.get(player.unique_id) is None
        entity_map.add(player)
        assert entity_map.get(player.unique_id) == player

    def test_destroyed_entities(self, entity_map):
        entities = [
            Player(location=utils.Coordinate(0, 0)),
            Player(location=utils.Coordinate(0, 0)),
            Player(location=utils.Coordinate(0, 0)),
            Player(location=utils.Coordinate(0, 0)),
            Player(location=utils.Coordinate(0, 0)),
        ]
        for entity in entities:
            entity_map.add(entity)

        assert len(entity_map.destroyed_entities()) == 0

        destroyed_entities = [
            entities[0],
            entities[2],
            entities[3]
        ]
        for entity in destroyed_entities:
            entity.destroyed = True

        assert len(entity_map.destroyed_entities()) == len(destroyed_entities)
        for entity in entity_map.destroyed_entities():
            destroyed_entities.remove(entity)
        assert len(destroyed_entities) == 0
