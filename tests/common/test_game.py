import python_bomberman.common.game.game as game
import python_bomberman.common.game.entities as entities
import python_bomberman.common.map as map
import python_bomberman.common.utils as utils
import pytest

class TestGameSuite:
    @pytest.fixture
    def empty_game_map(self):
        return map.Map(
            height=5,
            width=5
        )

    @pytest.fixture
    def populated_map(self, empty_game_map):
        empty_game_map.add(map.Player(utils.Coordinate(1, 1)))
        return empty_game_map

    @pytest.fixture
    def player_entity(self):
        return entities.Player(
            utils.Coordinate(1, 1)
        )

    @pytest.fixture
    def empty_game(self, empty_game_map):
        new_game = game.Game(empty_game_map)
        return new_game


    # for now, provided we test the attributes exclusively, the only thing
    # we need to test here is whether or not the game will automatically add
    # entities from the map to the game at init time.
    def test_init(self, populated_map):
        new_game = game.Game(populated_map)
        entity = new_game._board.get(utils.Coordinate(1, 1))
        assert entity is not None
        assert len(new_game.all_entities()) == 1

    def test_add(self, empty_game, player_entity):
        assert len(empty_game.all_entities()) == 0

        empty_game.add(player_entity)

        assert len(empty_game.all_entities()) == 1
        assert empty_game._board.get(player_entity.logical_location).entity == player_entity
        assert empty_game._entities.get(player_entity.unique_id) == player_entity

    def test_remove(self, empty_game, player_entity):
        self.test_add(empty_game, player_entity)
        empty_game.remove(player_entity)

        assert len(empty_game.all_entities()) == 0
        assert empty_game._board.get(player_entity.logical_location).entity is None
        assert empty_game._entities.get(player_entity.unique_id) is None

    def test_move(self, empty_game, player_entity):
        self.test_add(empty_game, player_entity)

        old_location = player_entity.logical_location
        new_location = utils.Coordinate(old_location.x + 1, old_location.y)

        assert player_entity.is_moving is False
        assert player_entity.logical_location == old_location
        assert empty_game._board.get(old_location).entity == player_entity

        empty_game.move(player_entity, new_location)

        assert player_entity.is_moving is True
        assert player_entity.logical_location is new_location
        assert empty_game._board.get(new_location).entity == player_entity

    def test_drop_bomb(self, empty_game, player_entity):
        empty_game.add(player_entity)

        space = empty_game._board.get(player_entity.logical_location)
        assert space.bomb is None
        assert player_entity.bombs == 1

        empty_game.drop_bomb(player_entity)

        assert player_entity.bombs == 0
        assert space.bomb is not None
        assert space.bomb.is_detonating is True


class TestBoardSuite:
    def test_init(self):
        pass

    def test_add(self):
        pass

    def test_remove(self):
        pass

    def test_blast_radius(self):
        pass


class TestEntityMapSuite:
    def test_init(self):
        pass

    def test_add(self):
        pass

    def test_remove(self):
        pass


class TestBoardSpaceSuite:
    def test_init(self):
        pass

    def test_has_collision(self):
        pass

    def test_add(self):
        pass

    def test_remove(self):
        pass

    def test_has_active_modifier(self):
        pass

    def test_has_active_fire(self):
        pass

    def test_has_indestructible_entities(self):
        pass

    def test_destructible_entities(self):
        pass