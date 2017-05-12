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
        empty_map.add(map.Player(utils.Coordinate(0, 0)))
        empty_map.add(map.Player(utils.Coordinate(3, 4)))
        empty_map.add(map.DestructibleWall(utils.Coordinate(1, 1)))
        empty_map.add(map.IndestructibleWall(utils.Coordinate(2, 2)))
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
            game_map=empty_map
        )

    @pytest.fixture
    def filled_game(self, game_configuration, filled_map):
        return game.Game(
            configuration=game_configuration,
            game_map=filled_map
        )

    @staticmethod
    def matching_num_entities(game_under_test):
        # validates the game board and the entity map for parity
        board_entities = [entity for row in game_under_test._board for entities in row for entity in entities]
        assert len(game_under_test.all_entities()) == len(board_entities)

    def _test_init(self, game_arg, map_arg, configuration):
        # make sure the number of entities match the number of map objects
        assert len(game_arg.all_entities()) == len(map_arg.all_objects())
        self.matching_num_entities(game_arg)

        # does the board match the map in terms of dimensions
        assert len(game_arg._board) == map_arg.width
        assert len(game_arg._board[0]) == map_arg.height

        # make sure the configuration is correct
        assert game_arg.configuration == configuration

    def test_init_empty(self, empty_game, empty_map, game_configuration):
        self._test_init(empty_game, empty_map, game_configuration)

    def test_init_filled(self, filled_game, filled_map, game_configuration):
        self._test_init(filled_game, filled_map, game_configuration)

    def test_add_entity(self, empty_game, new_entity):
        num_entities_before_add = len(empty_game.all_entities())
        uid = new_entity.unique_id
        loc = new_entity.logical_location

        empty_game.add(new_entity)
        assert len(empty_game.all_entities()) == num_entities_before_add + 1
        assert new_entity in empty_game.entities_at_location(location=loc)
        assert empty_game.entity_by_id(unique_id=uid) == new_entity

    def test_remove_entity(self, empty_game, new_entity):
        self.test_add_entity(empty_game, new_entity)

        num_entities_before_remove = len(empty_game.all_entities())
        uid = new_entity.unique_id
        loc = new_entity.logical_location

        empty_game.remove(new_entity)
        assert len(empty_game.all_entities()) == num_entities_before_remove - 1
        assert new_entity not in empty_game.entities_at_location(location=loc)
        assert empty_game.entity_by_id(unique_id=uid) is None
