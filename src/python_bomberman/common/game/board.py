from python_bomberman.common.game.constants import MovementDirection
import python_bomberman.common.game.entities as entities
import python_bomberman.common.utils as utils
from python_bomberman.common.game.exceptions import GameException


class Board:
    def __init__(self, dimensions):
        self.dimensions = dimensions
        self._board = [
            [
                BoardSpace(utils.Coordinate(x, y)) for y in range(0, dimensions.y)
            ] for x in range(0, dimensions.x)
        ]

    def add(self, entity):
        self.get(entity.logical_location).add(entity)

    def remove(self, entity):
        self.get(entity.logical_location).remove(entity)

    def get(self, location, direction=None, distance=None):
        if distance and direction:
            direction_map = {
                MovementDirection.UP: [location[0], location[1] - distance],
                MovementDirection.DOWN: [location[0], location[1] + distance],
                MovementDirection.LEFT: [location[0] - distance, location[1]],
                MovementDirection.RIGHT: [location[0] + distance, location[1]]
            }
            new_location = direction_map.get(direction, [*location])
            for index, (loc, dim) in enumerate(zip(new_location, self.dimensions)):
                if loc < 0:
                    new_location[index] += dim
                if loc >= dim:
                    new_location[index] -= dim
        elif not distance and not direction:
            new_location = [*location]
        else:
            raise GameException.incomplete_args(
                self.__class__, "get",
                {
                    "location": location,
                    "direction": direction,
                    "distance": distance
                }
            )

        new_location = utils.Coordinate(*new_location)
        if not 0 <= new_location.x < self.dimensions.x or not 0 <= new_location.y < self.dimensions.y:
            raise GameException.location_invalid(new_location)

        return self.get(new_location)

    def all_entities(self):
        return [entity for row in self._board for space in row for entity in space.all_entities()]

    def blast_radius(self, location, radius):
        to_return = [location]

        for direction in MovementDirection.all_directions():
            for distance in range(1, radius):
                space = self.get(location, direction, distance)
                if space.has_indestructible_entity():
                    break
                to_return.append(space)

        return to_return


class BoardSpace:
    def __init__(self, location):
        self.location = location
        self.modifier = None
        self.fire = None
        self.bomb = None
        self.entity = None

    def add(self, entity):
        attr = self._entity_to_attribute(entity)
        if getattr(self, attr, None) is not None:
            raise GameException.entity_at_location_exists(entity)
        setattr(self, attr, entity)

    def all_entities(self):
        return [entity for entity in [self.modifier, self.fire, self.bomb, self.entity] if entity is not None]

    def remove(self, entity):
        attr = self._entity_to_attribute(entity)
        if getattr(self, attr, None) is None:
            raise GameException.entity_at_location_doesnt_exist(entity)
        setattr(self, self._entity_to_attribute(entity), None)

    @staticmethod
    def _entity_to_attribute(entity):
        if isinstance(entity, entities.Bomb):
            return "bomb"
        elif isinstance(entity, entities.Modifier):
            return "modifier"
        elif isinstance(entity, entities.Fire):
            return "fire"
        return "entity"

    def occupied(self, entity):
        return getattr(self, self._entity_to_attribute(entity), None) is not None

    def has_modifier(self):
        return self.modifier is not None and not self.modifier.destroyed

    def has_fire(self):
        return self.fire is not None and not self.fire.destroyed

    def has_bomb(self):
        return self.bomb is not None and not self.bomb.destroyed

    def has_indestructible_entity(self):
        return self.entity is not None and not self.entity.can_be_destroyed

    def destroy_all(self):
        for entity in [entity for entity in self.all_entities() if entity.can_be_destroyed]:
            entity.destroyed = True
