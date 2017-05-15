import python_bomberman.common.game as game
import python_bomberman.common.map as map
import python_bomberman.common.utils as utils

import pytest
import time

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
    def player_entity(self):
        return game.Player(
            utils.Coordinate(2, 2)
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

    def _test_modifier(self, curr_game, player, modifier, attribute):
        original_attribute = getattr(player, attribute)

        curr_game.add(player)
        curr_game.add(modifier)
        curr_game.move(player, modifier.logical_location)
        time.sleep(player.movement_speed)
        curr_game.process()

        modified_attribute = getattr(player, attribute)
        assert (original_attribute + modifier.amount) == modified_attribute
        assert modifier.is_destroyed is True

    def test_init_empty(self, empty_game, empty_map, game_configuration):
        self._test_init(empty_game, empty_map, game_configuration)

    def test_init_filled(self, filled_game, filled_map, game_configuration):
        self._test_init(filled_game, filled_map, game_configuration)

    def test_add_entity(self, empty_game, player_entity):
        num_entities_before_add = len(empty_game.all_entities())
        uid = player_entity.unique_id
        loc = player_entity.logical_location

        empty_game.add(player_entity)
        assert len(empty_game.all_entities()) == num_entities_before_add + 1
        assert player_entity in empty_game.entities_at_location(location=loc)
        assert empty_game.entity_by_id(unique_id=uid) == player_entity

    def test_remove_entity(self, empty_game, player_entity):
        empty_game.add(player_entity)

        num_entities_before_remove = len(empty_game.all_entities())
        uid = player_entity.unique_id
        loc = player_entity.logical_location

        empty_game.remove(player_entity)
        assert len(empty_game.all_entities()) == num_entities_before_remove - 1
        assert player_entity not in empty_game.entities_at_location(location=loc)
        assert empty_game.entity_by_id(unique_id=uid) is None

    def test_bomb_detonate(self, empty_game, player_entity):
        orig_bomb_count = player_entity.bombs
        bomb_duration = player_entity.bomb_duration
        sleep_time = bomb_duration / 2.0

        empty_game.add(player_entity)
        empty_game.drop_bomb(player_entity)

        assert (orig_bomb_count - 1) == player_entity.bombs

        bomb = None
        for entity in empty_game.all_entities():
            if entity.can_detonate:
                bomb = entity
        assert bomb is not None

        time.sleep(bomb_duration/2)
        empty_game.process()
        assert 0 < bomb.bomb_duration <= bomb_duration

        time.sleep(bomb_duration/2)
        empty_game.process()
        assert bomb.is_detonated is True
        assert bomb.is_destroyed is True

    def test_bomb_modifier(self, empty_game, player_entity):
        bomb_modifier = game.BombModifier(
            location=utils.Coordinate(
                player_entity.logical_location[0]+1,
                player_entity.logical_location[1]
            )
        )
        self._test_modifier(empty_game, player_entity, bomb_modifier, "bombs")

    def test_movement_modifier(self, empty_game, player_entity):
        movement_modifier = game.MovementModifier(
            location=utils.Coordinate(
                player_entity.logical_location[0]+1,
                player_entity.logical_location[1]
            )
        )
        self._test_modifier(empty_game, player_entity, movement_modifier, "movement_speed")

    def test_fire_modifier(self, empty_game, player_entity):
        fire_modifier = game.FireModifier(
            location=utils.Coordinate(
                player_entity.logical_location[0]+1,
                player_entity.logical_location[1]
            )
        )
        self._test_modifier(empty_game, player_entity, fire_modifier, "fire_distance")

    def test_move_movable(self, empty_game, player_entity):
        empty_game.add(player_entity)

        original_location = player_entity.logical_location
        move_location = utils.Coordinate(player_entity.logical_location[0]+1, player_entity.logical_location[1])

        sleep_time = player_entity.movement_speed / 2.0

        # assert the initial move conditions are met
        empty_game.move(player_entity, move_location)
        assert player_entity.can_move and player_entity.is_moving
        assert player_entity.logical_location == move_location
        assert player_entity.physical_location != move_location

        # sleep for half the move time
        # and ensure that the player has moved in between the original and target locations
        time.sleep(sleep_time)
        empty_game.process()
        for (o_loc, p_loc, l_loc) in zip(original_location, player_entity.physical_location, player_entity.logical_location):
            if o_loc != l_loc:
                assert o_loc < p_loc < l_loc or l_loc < p_loc < o_loc

        # sleep for the remainder of the move time
        # and ensure that the player has reached their destination
        time.sleep(sleep_time)
        empty_game.process()
        assert player_entity.physical_location == player_entity.logical_location
        assert player_entity.logical_location == move_location


