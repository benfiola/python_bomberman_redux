import pytest
from python_bomberman.common.game.board import Board, BoardSpace
from python_bomberman.common.game.entities import Player, Bomb, Fire, BombModifier, IndestructibleWall
from python_bomberman.common.game.exceptions import GameException
from python_bomberman.common.game.constants import MovementDirection
import python_bomberman.common.utils as utils


class TestBoardSuite:
    @pytest.fixture
    def dimensions(self):
        return utils.Coordinate(5, 5)

    @pytest.fixture
    def board(self, dimensions):
        return Board(dimensions)

    @pytest.fixture
    def location(self):
        return utils.Coordinate(0, 0)

    @pytest.fixture
    def oob_location(self, dimensions):
        return utils.Coordinate(*dimensions)

    def test_init(self, board, dimensions):
        assert board is not None
        assert board.dimensions == dimensions
        assert len(board._board) == dimensions.x
        assert len(board._board[0]) == dimensions.y
        for row in board._board:
            for space in row:
                assert space is not None and isinstance(space, BoardSpace)

    def test_add(self, board, location, oob_location):
        player = Player(location)
        out_of_bounds = Player(oob_location)

        assert board.get(location).entity is None
        board.add(player)
        assert board.get(location).entity == player

        # we shouldn't allow any out of bounds entities to be added.
        with pytest.raises(GameException):
            board.add(out_of_bounds)

    def test_remove(self, board, location, oob_location):
        self.test_add(board, location, oob_location)
        player = board.get(location).entity
        out_of_bounds = Player(oob_location)

        board.remove(player)
        assert board.get(location).entity is None

        # while we shouldn't ever have an entity with a location that's out of bounds
        # we want to make sure we catch this when trying to remove a non-existant entity
        # that has an out of bounds location
        with pytest.raises(GameException):
            board.remove(out_of_bounds)

    def test_get(self, board, location, oob_location):
        dimensions = board.dimensions
        distance = 1
        # test getting an out of bounds location
        with pytest.raises(GameException):
            board.get(oob_location)
        # test out of bounds location with direction/distance modifiers
        with pytest.raises(GameException):
            board.get(oob_location, direction=MovementDirection.UP, distance=distance)
        # test getting a location with direction and not distance
        with pytest.raises(GameException):
            board.get(location, direction=MovementDirection.UP)
        # test getting a location with distance and not durection
        with pytest.raises(GameException):
            board.get(location, distance=distance)

        # make sure we get a space that matches the location we asked for
        space = board.get(location)
        assert space.location == location

        expected_map = {
            MovementDirection.UP: utils.Coordinate(location.x, (location.y - distance) % dimensions.y),
            MovementDirection.DOWN: utils.Coordinate(location.x, (location.y + distance) % dimensions.y),
            MovementDirection.LEFT: utils.Coordinate((location.x - distance) % dimensions.x, location.y),
            MovementDirection.RIGHT: utils.Coordinate((location.x + distance) % dimensions.x, location.y)
        }
        for direction in [MovementDirection.UP, MovementDirection.DOWN, MovementDirection.LEFT, MovementDirection.RIGHT]:
            space = board.get(location, direction=direction, distance=1)
            assert space.location == expected_map[direction]

    def test_blast_radius(self, board):
        dimensions = board.dimensions

        # first let's test an unobstructed blast radius call
        bomb_location = utils.Coordinate(2, 2)
        bomb_radius = 3
        locations = {
            utils.Coordinate(0, 2),
            utils.Coordinate(1, 2),
            utils.Coordinate(2, 2),
            utils.Coordinate(3, 2),
            utils.Coordinate(4, 2),
            utils.Coordinate(2, 0),
            utils.Coordinate(2, 1),
            utils.Coordinate(2, 3),
            utils.Coordinate(2, 4)
        }
        spaces = board.blast_radius(bomb_location, radius=bomb_radius)
        for space in spaces:
            locations.remove(space.location)
        assert len(locations) == 0

        # now a more complicated test case that tests 'wrap around' functionality
        # as well as obstructions
        # D _ _ _ _
        # B _ I I _
        # _ _ _ _ _
        # _ _ _ _ _
        # _ _ _ _ _
        #
        # and we expect the blast radius to be
        # X _ _ _ _
        # X X _ _ X
        # X _ _ _ _
        # X _ _ _ _
        # X _ _ _ _
        # where D is an entity that can be blown up
        # where I is an entity that can't be blown up
        # where B is the bomb location
        # where X indicates a location returned in a call to blast_radius

        bomb_location = utils.Coordinate(0, 1)
        player = Player(location=utils.Coordinate(0, 0))
        indestructible_wall = IndestructibleWall(location=utils.Coordinate(2, 1))
        other_bomb = Bomb(utils.Coordinate(dimensions.x-2, 1), radius=0)
        board.add(player)
        board.add(indestructible_wall)
        board.add(other_bomb)
        spaces = board.blast_radius(bomb_location, bomb_radius)
        locations = {
            utils.Coordinate(0, 0),
            utils.Coordinate(0, 1),
            utils.Coordinate(0, 2),
            utils.Coordinate(0, 3),
            utils.Coordinate(0, 4),
            utils.Coordinate(1, 1),
            utils.Coordinate(dimensions.x-1, 1),
        }
        for space in spaces:
            locations.remove(space.location)
        assert len(locations) == 0


class TestBoardSpaceSuite:
    @pytest.fixture
    def location(self):
        return utils.Coordinate(0, 0)

    @pytest.fixture
    def board_space(self, location):
        return BoardSpace(location=location)

    def test_init(self, board_space, location):
        assert location == board_space.location
        assert board_space.modifier is None
        assert board_space.fire is None
        assert board_space.entity is None
        assert board_space.bomb is None

    def test_add(self, board_space, location):
        entity = Player(location)
        bomb = Bomb(location, radius=0)
        fire = Fire(location)
        modifier = BombModifier(location)

        board_space.add(entity)
        board_space.add(bomb)
        board_space.add(fire)
        board_space.add(modifier)

        assert board_space.entity == entity
        assert board_space.bomb == bomb
        assert board_space.fire == fire
        assert board_space.modifier == modifier

        with pytest.raises(GameException):
            board_space.add(entity)

    def test_remove(self, board_space, location):
        self.test_add(board_space, location)

        entity = board_space.entity
        diff_entity = Player(entity.logical_location)
        bomb = board_space.bomb
        fire = board_space.fire
        modifier = board_space.modifier

        board_space.remove(entity)
        assert board_space.entity is None
        board_space.remove(bomb)
        assert board_space.bomb is None
        board_space.remove(fire)
        assert board_space.fire is None
        board_space.remove(modifier)
        assert board_space.modifier is None

        with pytest.raises(GameException):
            board_space.remove(entity)
        with pytest.raises(GameException):
            board_space.remove(diff_entity)

    def test_occupied(self, board_space, location):
        self.test_add(board_space, location)

        entity = board_space.entity
        bomb = board_space.bomb
        fire = board_space.fire
        modifier = board_space.modifier

        assert board_space.occupied(entity) is True
        entity.destroyed = True
        assert board_space.occupied(entity) is False
        board_space.remove(entity)
        assert board_space.occupied(entity) is False
        assert board_space.occupied(bomb) is True
        bomb.destroyed = True
        assert board_space.occupied(bomb) is False
        board_space.remove(bomb)
        assert board_space.occupied(bomb) is False
        assert board_space.occupied(fire) is True
        fire.destroyed = True
        assert board_space.occupied(fire) is False
        board_space.remove(fire)
        assert board_space.occupied(fire) is False
        assert board_space.occupied(modifier) is True
        modifier.destroyed = True
        assert board_space.occupied(modifier) is False
        board_space.remove(modifier)
        assert board_space.occupied(modifier) is False

    def test_has_modifier(self, board_space, location):
        modifier = BombModifier(location)
        assert board_space.has_modifier() is False
        board_space.add(modifier)
        assert board_space.has_modifier() is True
        modifier.destroyed = True
        assert board_space.has_modifier() is False

    def test_has_fire(self, board_space, location):
        fire = Fire(location)
        assert board_space.has_fire() is False
        board_space.add(fire)
        assert board_space.has_fire() is True
        fire.destroyed = True
        assert board_space.has_fire() is False

    def test_has_bomb(self, board_space, location):
        bomb = Bomb(location, 0)
        assert board_space.has_bomb() is False
        board_space.add(bomb)
        assert board_space.has_bomb() is True
        bomb.destroyed = True
        assert board_space.has_bomb() is False

    def test_has_indestructible_entity(self, board_space, location):
        assert board_space.has_indestructible_entity() is False

        player = Player(location)
        board_space.add(player)
        assert board_space.has_indestructible_entity() is False
        board_space.remove(player)

        bomb = Bomb(location, 0)
        board_space.add(bomb)
        assert board_space.has_indestructible_entity() is True
        board_space.add(player)
        assert board_space.has_indestructible_entity() is True
        board_space.remove(bomb)
        assert board_space.has_indestructible_entity() is False
        board_space.remove(player)

        wall = IndestructibleWall(location)
        board_space.add(wall)
        assert board_space.has_indestructible_entity() is True
        board_space.remove(wall)

    def test_destroy_all(self, board_space, location):
        self.test_add(board_space, location)

        player = board_space.entity
        bomb = board_space.bomb
        fire = board_space.fire
        modifier = board_space.modifier

        board_space.destroy_all()
        assert player.destroyed is True
        assert bomb.destroyed is False
        assert fire.destroyed is True
        assert modifier.destroyed is True
