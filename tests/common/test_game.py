import python_bomberman.common.game.game as game
import python_bomberman.common.game.entities as entities
import python_bomberman.common.map as map
import python_bomberman.common.utils as utils
import pytest
import time


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

    @pytest.fixture
    def fire(self):
        return entities.Fire(
            utils.Coordinate(1, 1)
        )

    @pytest.fixture
    def bomb_modifier(self):
        return entities.BombModifier(utils.Coordinate(1, 1))

    @pytest.fixture
    def fire_modifier(self):
        return entities.FireModifier(utils.Coordinate(1, 1))

    @pytest.fixture
    def movement_modifier(self):
        return entities.MovementModifier(utils.Coordinate(1, 1))

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
        assert player_entity.physical_location == old_location
        assert player_entity.logical_location == new_location
        assert empty_game._board.get(new_location).entity == player_entity

    def test_process_move(self, empty_game, player_entity):
        self.test_move(empty_game, player_entity)
        distance = abs(player_entity.logical_location.x - player_entity.physical_location.x)
        time_to_sleep = (distance/player_entity.movement_speed)
        old_location = player_entity.physical_location
        new_location = player_entity.logical_location

        time.sleep(time_to_sleep/2.0)
        empty_game.process()
        assert old_location < player_entity.physical_location < new_location
        assert player_entity.is_moving is True

        time.sleep(time_to_sleep/2.0)
        empty_game.process()
        assert player_entity.is_moving is False
        assert player_entity.physical_location == new_location
        assert player_entity.logical_location == new_location

    def test_drop_bomb(self, empty_game, player_entity):
        empty_game.add(player_entity)

        space = empty_game._board.get(player_entity.logical_location)
        assert space.bomb is None
        assert player_entity.bombs == 1

        empty_game.drop_bomb(player_entity)

        assert player_entity.bombs == 0
        assert space.bomb is not None
        assert space.bomb.is_detonating is True

    def test_process_bomb(self, empty_game, player_entity):
        self.test_drop_bomb(empty_game, player_entity)

        bomb_count = player_entity.bombs
        space = empty_game._board.get(player_entity.logical_location)
        bomb = space.bomb

        bomb_duration = bomb.bomb_duration

        time.sleep(bomb_duration/2.0)
        empty_game.process()
        assert bomb_duration > bomb.bomb_duration > 0

        time.sleep(bomb_duration/2.0)
        empty_game.process()
        assert bomb.bomb_duration <= 0
        assert bomb.is_detonating is False
        assert bomb.is_destroyed is True
        assert player_entity.bombs == bomb_count + 1

        # since the player hasn't moved since dropping the bomb
        # they should also be destroyed
        assert player_entity.is_destroyed is True

    def test_process_fire(self, empty_game, fire):
        empty_game.add(fire)
        fire.is_burning = True
        fire_duration = fire.fire_duration

        time.sleep(fire_duration/2.0)
        empty_game.process()
        assert fire_duration > fire.fire_duration > 0
        assert fire.is_burning is True

        time.sleep(fire_duration/2.0)
        empty_game.process()
        assert fire.fire_duration <= 0
        assert fire.is_burning is False
        assert fire.is_destroyed is True

    def _test_modifier(self, curr_game, curr_player_entity, curr_modifier, attribute):
        old_val = getattr(curr_player_entity, attribute)

        # test add modifier first, then player
        curr_game.add(curr_modifier)
        curr_game.add(curr_player_entity)
        assert getattr(curr_player_entity, attribute) == (old_val + curr_modifier.amount)
        assert curr_modifier.is_destroyed is True

        # remove the modifier, and reset the modified player attribute
        curr_game.remove(curr_modifier)
        setattr(curr_player_entity, attribute, old_val)

        curr_game.add(curr_modifier)
        assert getattr(curr_player_entity, attribute) == (old_val + curr_modifier.amount)
        assert curr_modifier.is_destroyed is True

    def test_process_movement_modifier(self, empty_game, player_entity, movement_modifier):
        self._test_modifier(empty_game, player_entity, movement_modifier, "movement_speed")

    def test_process_fire_distance_modifier(self, empty_game, player_entity, fire_modifier):
        self._test_modifier(empty_game, player_entity, fire_modifier, "fire_distance")

    def test_process_bomb_modifier(self, empty_game, player_entity, bomb_modifier):
        self._test_modifier(empty_game, player_entity, bomb_modifier, "bombs")

    def test_process_remove_destroyed_entity(self, empty_game, player_entity):
        empty_game.add(player_entity)
        assert player_entity in empty_game.all_entities()
        assert empty_game._entities.get(player_entity.unique_id) == player_entity
        assert player_entity in empty_game._board.get(player_entity.logical_location).all_entities()

        player_entity.is_destroyed = True
        empty_game.process()
        assert player_entity not in empty_game.all_entities()
        assert empty_game._entities.get(player_entity.unique_id) is None
        assert player_entity not in empty_game._board.get(player_entity.logical_location).all_entities()

    def test_process_move_into_modifier(self, empty_game, player_entity):
        distance = 1
        modifier_location = utils.Coordinate(player_entity.logical_location.x + distance, player_entity.logical_location.y)
        modifier = entities.BombModifier(modifier_location)
        modifier_attribute = "bombs"
        movement_duration = distance/player_entity.movement_speed
        old_attribute_value = getattr(player_entity, modifier_attribute)

        empty_game.add(player_entity)
        empty_game.add(modifier)
        empty_game.move(player_entity, modifier_location)
        time.sleep(movement_duration)
        empty_game.process()

        assert getattr(player_entity, modifier_attribute) == old_attribute_value + 1
        assert modifier.is_destroyed is True

    def test_process_move_into_fire(self, empty_game, player_entity):
        distance = 1
        fire_location = utils.Coordinate(player_entity.logical_location.x + distance, player_entity.logical_location.y)
        fire = entities.Fire(fire_location)
        fire.is_burning = True
        movement_duration = distance / player_entity.movement_speed

        empty_game.add(player_entity)
        empty_game.add(fire)
        empty_game.move(player_entity, fire_location)
        time.sleep(movement_duration)
        empty_game.process()
        assert player_entity.is_destroyed is True


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