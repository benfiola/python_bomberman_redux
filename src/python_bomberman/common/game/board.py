from python_bomberman.common.game.constants import MovementDirection
import python_bomberman.common.game.entities as entities
import python_bomberman.common.utils as utils
from python_bomberman.common.game.exceptions import GameException


class Board:
    """
    This is a data container that maps location data to entities via a 2D array.
    """
    def __init__(self, dimensions):
        self.dimensions = dimensions
        self._board = [
            [
                BoardSpace(utils.Coordinate(x, y)) for y in range(0, dimensions.y)
            ] for x in range(0, dimensions.x)
        ]

    def add(self, entity):
        """
        Adds an entity to an underlying board space in the board
        :param entity:
        :return:
        """
        self.get(entity.logical_location).add(entity)

    def remove(self, entity):
        """
        Removes an entity from an underlying board space in the board.

        This is provided mainly because there should never be a point
        where we're trying to remove an unknown entity from the board,
        so while this object is mainly a mapping for locations of entities
        to the entities themselves, we don't want to provide any sort of
        interface that says 'remove arbitrarily an element at this location'.
        :param entity:
        :return:
        """
        self.get(entity.logical_location).remove(entity)

    def get(self, location, direction=None, distance=None):
        """
        Retrieves a board space specified by the given location.

        Additionally, you can provide direction and distance attributes
        that, together with the location argument, will get you the space
        identified by the location + distance, direction.

        Location is checked to see if it's in bounds.
        If direction + distance yields a space that would otherwise be out of bounds,
        we wrap to the other side of the board.

        You must provide both distance and direction if you're going to use these
        options.
        :param location:
        :param direction:
        :param distance:
        :return:
        """
        if not 0 <= location.x < self.dimensions.x or not 0 <= location.y < self.dimensions.y:
            raise GameException.location_invalid(location)

        if distance is not None and direction is not None:
            direction_map = {
                MovementDirection.UP: utils.Coordinate(location[0], (location[1] - distance) % self.dimensions.y),
                MovementDirection.DOWN: utils.Coordinate(location[0], (location[1] + distance) % self.dimensions.y),
                MovementDirection.LEFT: utils.Coordinate((location[0] - distance) % self.dimensions.x, location[1]),
                MovementDirection.RIGHT: utils.Coordinate((location[0] + distance) % self.dimensions.x, location[1])
            }
            new_location = utils.Coordinate(*direction_map.get(direction, location))
        elif distance is None and direction is None:
            new_location = location
        else:
            raise GameException.incomplete_args(
                self.__class__, "get",
                {
                    "location": location,
                    "direction": direction,
                    "distance": distance
                }
            )
        return self._board[new_location.x][new_location.y]

    def all_entities(self):
        """
        Convenience method to get all entities that the board is aware of.
        :return:
        """
        return [entity for row in self._board for space in row for entity in space.all_entities()]

    def blast_radius(self, location, radius):
        """
        Convenience method that, given a bomb location and radius, will return
        all board spaces that will be 'included' in the blast (taking into consideration
        the event that an entity might be indestructible, cutting short the blast in
        that general direction).
        :param location:
        :param radius:
        :return:
        """
        locations = {location}

        for direction in MovementDirection.all_directions():
            for distance in range(1, radius):
                space = self.get(location, direction=direction, distance=distance)
                if space.has_indestructible_entity():
                    break
                locations.add(space.location)

        return [self.get(space_location) for space_location in list(locations)]


class BoardSpace:
    """
    A board space is a container for a single location on the game board.
    There are a few things that can co-exist at a single location in a
    bomberman game, which predicated me writing it out as a class instead.
    """
    def __init__(self, location):
        self.location = location
        self.modifier = None
        self.fire = None
        self.bomb = None
        self.entity = None

    def add(self, entity):
        """
        Adds an entity to this board space.

        If there's an entity already in this space, an exception will be thrown.
        :param entity:
        :return:
        """
        attr = self._entity_to_attribute(entity)
        if getattr(self, attr, None) is not None:
            raise GameException.entity_at_location_exists(entity)
        setattr(self, attr, entity)

    def all_entities(self):
        """
        Convenience method to get all entities in this board space.
        :return:
        """
        return [entity for entity in [self.modifier, self.fire, self.bomb, self.entity] if entity is not None]

    def remove(self, entity):
        """
        Removes an entity from this board space.

        If the entity passed into the method doesn't match the entity in the space, an exception will be thrown.
        If there is no entity to remove in this space, an exception will be thrown.
        :param entity:
        :return:
        """
        attr = self._entity_to_attribute(entity)
        found_entity = getattr(self, attr, None)
        if getattr(self, attr, None) is None:
            raise GameException.entity_at_location_doesnt_exist(entity)
        if found_entity != entity:
            raise GameException.entity_to_remove_doesnt_match(entity, found_entity)
        setattr(self, self._entity_to_attribute(entity), None)

    @staticmethod
    def _entity_to_attribute(entity):
        """
        This is a way to define how an entity passed into an occupied/add/remove method
        maps to a particular attribute of this object.
        :param entity:
        :return:
        """
        if isinstance(entity, entities.Bomb):
            return "bomb"
        elif isinstance(entity, entities.Modifier):
            return "modifier"
        elif isinstance(entity, entities.Fire):
            return "fire"
        return "entity"

    def occupied(self, entity):
        """
        Checks to see if this space is occupied for a given entity type.
        Will check to see if the entity exists AND if the entity is not destroyed.
        :param entity:
        :return:
        """
        entity = getattr(self, self._entity_to_attribute(entity), None)
        return entity is not None and not entity.destroyed

    def has_modifier(self):
        """
        Convenience method to return whether or not there's a modifier in this location
        that can be picked up by another entity.
        :return:
        """
        return self.modifier is not None and not self.modifier.destroyed

    def has_fire(self):
        """
        Convenience method to return whether or not there's a fire in this location
        that will burn another entity.
        :return:
        """
        return self.fire is not None and not self.fire.destroyed

    def has_bomb(self):
        """
        Convenience method to return whether or not there's a bomb in this location
        that is still active.
        :return:
        """
        return self.bomb is not None and not self.bomb.destroyed

    def has_indestructible_entity(self):
        """
        Convenience method to return whether or not this space is occupied by
        any entity that will stop the spread of a bomb blast.
        :return:
        """
        return (
            self.entity is not None and not self.entity.can_destroy and not self.entity.destroyed
        ) or (
            self.bomb is not None and not self.bomb.destroyed
        )

    def destroy_all(self):
        """
        If this space is included in a bomb's blast radius, this will set the destroyed
        flag for all entities that can be destroyed.
        :return:
        """
        for entity in [entity for entity in self.all_entities() if entity.can_destroy]:
            entity.destroyed = True
