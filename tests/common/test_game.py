import python_bomberman.common.game as game
import python_bomberman.common.map as map
import python_bomberman.common.utils as utils

import pytest

class TestSuite:
    @pytest.fixture
    def empty_map(self):
        new_map = map.Map(5, 5, name="test")
        return new_map

    @pytest.fixture
    def filled_map(self, empty_map):
        empty_map.add_object(map.Player(utils.Coordinate(0, 0)))
        empty_map.add_object(map.Player(utils.Coordinate(3, 4)))
        empty_map.add_object(map.DestructibleWall(utils.Coordinate(1, 1)))
        empty_map.add_object(map.IndestructibleWall(utils.Coordinate(2, 2)))
        return empty_map

    @pytest.fixture
    def game_configuration(self):
        return game.GameConfiguration()

    @pytest.fixture
    def new_entity(self):
        return game.Player(
            utils.Coordinate(1, 0)
        )

    @pytest.fixture
    def empty_game(self, game_configuration, empty_map):
        return game.Game(
            configuration=game_configuration,
            map=empty_map
        )

    @pytest.fixture
    def filled_game(self, game_configuration, filled_map):
        return game.Game(
            configuration=game_configuration,
            map=filled_map
        )

    @staticmethod
    def matching_num_entities(game_under_test):
        # validates the game board and the entity map for parity
        board_entities = [entity for row in game_under_test._board for entity in row if entity is not None]
        assert len(game_under_test.get_entities()) == len(board_entities)

    def _test_init(self, game, map, configuration):
        # make sure the number of entities match the number of map objects
        assert len(game.get_entities()) == len(map.get_objects())
        self.matching_num_entities(game)

        # does the board match the map in terms of dimensions
        assert len(game._board) == map.width
        assert len(game._board[0]) == map.height

        # make sure the configuration is correct
        assert game.configuration == configuration

    def test_init_empty(self, empty_game, empty_map, game_configuration):
        self._test_init(empty_game, empty_map, game_configuration)

    def test_init_filled(self, filled_game, filled_map, game_configuration):
        self._test_init(filled_game, filled_map, game_configuration)

    def test_add_entity(self, empty_game, new_entity):
        num_entities_before_add = len(empty_game.get_entities())
        uid = new_entity.unique_id
        loc = new_entity.logical_location

        empty_game.add_entity(new_entity)
        assert len(empty_game.get_entities()) == num_entities_before_add + 1
        assert empty_game.get_entity(location=loc) == new_entity
        assert empty_game.get_entity(unique_id=uid) == new_entity

    def test_remove_entity(self, empty_game, new_entity):
        self.test_add_entity(empty_game, new_entity)

        num_entities_before_remove = len(empty_game.get_entities())
        uid = new_entity.unique_id
        loc = new_entity.logical_location

        empty_game.remove_entity(new_entity)
        assert len(empty_game.get_entities()) == num_entities_before_remove - 1
        assert empty_game.get_entity(location=loc) is None
        assert empty_game.get_entity(unique_id=uid) is None
