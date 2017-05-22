from python_bomberman.common.game.exceptions import GameException
from python_bomberman.common.game.entities import Modifier, Fire, Bomb, Collideable
from python_bomberman.common.utils import Coordinate


class BoardSpace(object):
    def __init__(self, location):
        self.location = location
        self.modifier = None
        self.entity = None
        self.bomb = None
        self.fire = None

    @staticmethod
    def _space_attr(entity):
        if isinstance(entity, Bomb):
            return "bomb"
        elif isinstance(entity, Modifier):
            return "modifier"
        elif isinstance(entity, Fire):
            return "fire"
        else:
            return "entity"

    def mark_entities_for_destruction(self):
        if self.modifier:
            self.modifier.is_destroyed = True
        if self.entity:
            self.entity.is_destroyed = True

    def has_collision(self):
        return self.bomb or isinstance(self.entity, Collideable)

    def add(self, entity):
        attr = self._space_attr(entity)
        if getattr(self, attr, None):
            raise GameException.space_occupied(self.location, attr, entity)
        setattr(self, attr, entity)

    def remove(self, entity):
        attr = self._space_attr(entity)
        if not getattr(self, attr, None):
            raise GameException.space_not_occupied(self.location, attr, entity)
        setattr(self, attr, None)


class Board(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._spaces = [[BoardSpace(Coordinate(x, y)) for y in range(0, height)] for x in range(0, width)]

    def _all_entities(self):
        to_return = []
        for column in self._spaces:
            for space in column:
                if space.entity:
                    to_return.append(space.entity)
                if space.modifier:
                    to_return.append(space.modifier)
                if space.fire:
                    to_return.append(space.fire)
        return to_return

    def get_space(self, location):
        return self._spaces[location.x][location.y]

    def add(self, entity):
        self.get_space(entity.logical_location).add(entity)

    def remove(self, entity):
        self.get_space(entity.logical_location).remove(entity)
