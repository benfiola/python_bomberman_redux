from python_bomberman.common.game.board_space import BoardSpace
from python_bomberman.common.game.movement_direction import MovementDirection

class Board:
    def __init__(self, dimensions):
        self.dimensions = dimensions
        self._board = [[BoardSpace() for _ in range(0, dimensions.y)] for _ in range(0, dimensions.x)]

    def add(self, entity):
        self._board[entity.logical_location.x][entity.logical_location.y].add(entity)

    def remove(self, entity):
        self._board[entity.logical_location.x][entity.logical_location.y].remove(entity)

    def get(self, location):
        return self._board[location.x][location.y]

    def all_entities(self):
        return [entity for row in self._board for space in row for entity in space.all_entities()]

    def blast_radius(self, location, radius):
        return []

    def get_coordinate(self, location, direction, distance=1):
        new_location = [
            *location
        ]
        if direction == MovementDirection.UP:
            new_location[1] -= distance
        elif direction == MovementDirection.DOWN:
            new_location[1] += distance
        elif direction == MovementDirection.LEFT:
            new_location[0] -= distance
        elif direction == MovementDirection.RIGHT:
            new_location[0] += distance
        for index, (loc, dim) in enumerate(zip(new_location, self.dimensions)):
            if loc < 0:
                new_location[index] += dim
            if loc >= dim:
                new_location[index] -= dim
        return utils.Coordinate(*new_location)