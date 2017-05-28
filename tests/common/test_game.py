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
    @pytest.fixture
    def board(self):
        return game.Board(1, 1)

    @pytest.fixture
    def entity(self):
        return entities.Player(utils.Coordinate(0, 0))

    def test_init(self):
        width = 1
        height = 2
        board = game.Board(width, height)
        assert board.width == width
        assert board.height == height
        assert len(board._board) == width
        assert len(board._board[0]) == height
        for row in board._board:
            for space in row:
                assert isinstance(space, game.BoardSpace)
        assert len(board.all_entities()) == 0

    def test_add(self, board, entity):
        assert len(board.all_entities()) == 0
        board.add(entity)
        assert len(board.all_entities()) == 1
        assert entity in board.all_entities()

    def test_remove(self, board, entity):
        self.test_add(board, entity)
        board.remove(entity)
        assert len(board.all_entities()) == 0
        assert entity not in board.all_entities()

    def test_blast_radius(self):
        board = game.Board(5, 5)
        player = entities.Player(utils.Coordinate(2, 2))
        bomb = entities.Bomb(location=utils.Coordinate(2, 2), owner=player)
        board.add(player)
        board.add(bomb)
        walls = [
            entities.IndestructibleWall(utils.Coordinate(2, 0)),
            entities.IndestructibleWall(utils.Coordinate(3, 2))
        ]
        for wall in walls:
            board.add(wall)
        locations = [
            utils.Coordinate(2, 1),
            utils.Coordinate(0, 2),
            utils.Coordinate(1, 2),
            utils.Coordinate(2, 2),
            utils.Coordinate(2, 3),
            utils.Coordinate(2, 4)
        ]
        blast_radius = board.blast_radius(bomb.logical_location, bomb.fire_distance)
        assert len(locations) == len(blast_radius)
        for location in locations:
            assert location in blast_radius


class TestEntityMapSuite:
    @pytest.fixture
    def entity_map(self):
        return game.EntityMap()

    @pytest.fixture
    def entity(self):
        return entities.Player(utils.Coordinate(0, 0))

    def test_init(self, entity_map):
        assert len(entity_map._entities) == 0
        assert len(entity_map.all_entities()) == 0

    def test_add(self, entity_map, entity):
        assert len(entity_map.all_entities()) == 0
        entity_map.add(entity)
        assert entity_map.get(entity.unique_id) == entity
        assert len(entity_map.all_entities()) == 1

    def test_remove(self, entity_map, entity):
        self.test_add(entity_map, entity)
        entity_map.remove(entity)
        assert entity_map.get(entity.unique_id) is None
        assert len(entity_map.all_entities()) == 0


class TestBoardSpaceSuite:
    @pytest.fixture
    def space(self):
        return game.BoardSpace()

    @pytest.fixture
    def fire(self):
        return entities.Fire(utils.Coordinate(0, 0))

    @pytest.fixture
    def modifier(self):
        return entities.BombModifier(utils.Coordinate(0, 0))

    @pytest.fixture
    def bomb(self, player):
        return entities.Bomb(location=utils.Coordinate(0, 0), owner=player)

    @pytest.fixture
    def player(self):
        return entities.Player(utils.Coordinate(0, 0))

    @pytest.fixture
    def indestructible_wall(self):
        return entities.IndestructibleWall(utils.Coordinate(0, 0))

    @pytest.fixture
    def destructible_wall(self):
        return entities.DestructibleWall(utils.Coordinate(0, 0))

    def test_init(self, space):
        assert space.modifier is None
        assert space.fire is None
        assert space.entity is None
        assert space.bomb is None

    def test_has_collision(self, space, player, fire, modifier, bomb):
        assert space.has_collision() is False
        self.test_add_fire(space, fire)
        assert space.has_collision() is False
        self.test_add_modifier(space, modifier)
        assert space.has_collision() is False
        self.test_add_entity(space, player)
        assert space.has_collision() is True
        self.test_remove_entity(space, player)
        assert space.has_collision() is False
        self.test_add_bomb(space, bomb)
        assert space.has_collision() is True
        self.test_remove_bomb(space, bomb)
        assert space.has_collision() is False

    def test_add_entity(self, space, player):
        space.add(player)
        assert space.entity == player

    def test_add_fire(self, space, fire):
        space.add(fire)
        assert space.fire == fire

    def test_add_modifier(self, space, modifier):
        space.add(modifier)
        assert space.modifier == modifier

    def test_add_bomb(self, space, bomb):
        space.add(bomb)
        assert space.bomb == bomb

    def test_remove_entity(self, space, player):
        self.test_add_entity(space, player)
        space.remove(player)
        assert space.entity is None

    def test_remove_fire(self, space, fire):
        self.test_add_fire(space, fire)
        space.remove(fire)
        assert space.fire is None

    def test_remove_modifier(self, space, modifier):
        self.test_add_modifier(space, modifier)
        space.remove(modifier)
        assert space.modifier is None

    def test_remove_bomb(self, space, bomb):
        self.test_add_bomb(space, bomb)
        space.remove(bomb)
        assert space.bomb is None

    def test_has_active_modifier(self, space, modifier):
        assert space.has_active_modifier() is False
        self.test_add_modifier(space, modifier)
        assert space.has_active_modifier() is True
        modifier.is_destroyed = True
        assert space.has_active_modifier() is False

    def test_has_active_fire(self, space, fire):
        assert space.has_active_fire() is False
        self.test_add_fire(space, fire)
        assert space.has_active_fire() is False
        fire.is_burning = True
        assert space.has_active_fire() is True
        fire.is_destroyed = True
        assert space.has_active_fire() is False

    def test_has_indestructible_entities(self, space, indestructible_wall):
        assert space.has_indestructible_entities() is False
        space.add(indestructible_wall)
        assert space.has_indestructible_entities() is True

    def test_destructible_entities(self, space, modifier, fire, bomb, indestructible_wall):
        self.test_add_entity(space, indestructible_wall)
        self.test_add_fire(space, fire)
        self.test_add_bomb(space, bomb)
        self.test_add_modifier(space, modifier)
        destructible_entities = [
            modifier,
            fire,
            bomb
        ]
        assert len(destructible_entities) == len(space.destructible_entities())
        for entity in destructible_entities:
            assert entity in (space.destructible_entities())