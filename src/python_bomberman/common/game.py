from python_bomberman.common.logging import logger
from python_bomberman.common.utils import Coordinate
from uuid import uuid4
import time
import math


@logger.create()
class Game(object):
    def __init__(self, map, configuration):
        self.configuration = configuration
        self._board = [[None for _ in range(0, map.height)] for _ in range(0, map.width)]
        self._entities = {}

        for entity in self._convert_map_objects(map.get_objects()):
            self.add_entity(entity)

    @staticmethod
    def _convert_map_objects(map_objs):
        entity_classes = {cls.identifier: cls for cls in Entity.__subclasses__() if hasattr(cls, "identifier")}
        return [
            entity_classes[map_obj.identifier](
                location=map_obj.location
            ) for map_obj in map_objs if map_obj.identifier in entity_classes
        ]

    def get_entities(self):
        return self._entities.values()

    def get_entity(self, location=None, unique_id=None):
        if location:
            return self._board[location.x][location.y]
        if unique_id and unique_id in self._entities:
            return self._entities[unique_id]
        return None

    def move_entity(self, entity, location):
        """
        Sets up an entity to be further processed for movement given a location.
        :param entity: Entity that needs to be moved
        :param location: desired Coordinate to move Entity to.
        :return: 
        """
        if not self._will_collide(location):
            # when moving, an entity needs to 'claim' a space before it moves to prevent
            # race conditions where two players might move into the same space.
            # in order to do so, we immediately assume the player is going to move to the target location
            # and we set the entity to reside at that location in the _board object.
            # however, if there are modifiers on that spot, we need a way to remember that those existed
            # in the event that a player moves away from their 'claimed' spot before they arrive.
            #
            # so, if an entity is moving, it drops its claimed modifier at its current 'logical_location'
            # a logical_location is current location/target of movement depending on movement state
            # and an entity only has a claimed modifier if it's moving, otherwise it's None.
            self._board[entity.logical_location.x][entity.logical_location.y] = entity.movement_claimed_modifier
            modifier = self.get_entity(location=location)
            entity.set_to_move(location, modifier)
            self._board[entity.logical_location.x][entity.logical_location.y] = entity

    def process(self):
        """
        Processes the gameboard and updates entities currently undergoing time-based modification.
        :return: None
        """
        for entity in self.get_entities():
            if entity.moving:
                entity.move()

    def add_entity(self, entity):
        """
        Will add an entity to both the entity map as well as the gameboard.
        :param entity: Entity to be added
        :return: None
        """
        self._entities[entity.unique_id] = entity
        self._board[entity.logical_location.x][entity.logical_location.y] = entity

    def remove_entity(self, entity):
        """
        Will remove an entity from both the entity map as well as the gameboard.
        :param entity: Entity to be removed
        :return: None
        """
        self._entities.pop(entity.unique_id)
        self._board[entity.logical_location.x][entity.logical_location.y] = None

    def _will_collide(self, location):
        """
        Checks to see if a given Coordinate is occupied by a solid entity.
        :param location: Location where collision check is performed
        :return: bool indicating whether spot is occupied
        """
        potential_entity = self.get_entity(location=location)
        return potential_entity is not None and potential_entity.solid


class Entity(object):
    def __init__(self, location, unique_id):
        if unique_id is None:
            unique_id = uuid4()
        self.logical_location = location
        self.physical_location = location
        self.unique_id = unique_id

        # state related attributes
        self.moving = False
        self.movement_claimed_modifier = None
        self.movement_speed = None
        self.last_update = None

        # properties
        self.solid = True
        self.modifier = False

    def set_to_move(self, location, modifier=None):
        """
        Sets up an entity to move.  
        :param location: Coordinate to move to
        :param modifier: Modifier at location, if there is one.
        :return: None
        """
        # if this entity doesnt have a movement speed, it's assumed
        # that we want to simply teleport it over to where it needs to be
        # otherwise, we set up the proper state and delegate to the process
        # methods to move the entity.
        if not self.movement_speed:
            self.physical_location = location
        else:
            self.moving = True
            self.movement_claimed_modifier = modifier
            self.last_update = time.time()
            self.logical_location = location

    def _new_movement_location(self, duration):
        """
        Calculates the new movement location using self.logical_location as the target
        and self.physical_location as the current location
        :param duration: Duration of time since last update in seconds
        :return: a Coordinate object representing the new location of the entity.
        """
        list_vec = []
        for index, (l_loc, p_loc) in enumerate(zip(self.logical_location, self.physical_location)):
            # We tend to move in a single direction making this pretty easy.
            # If our current location and target location are the same, we're not moving
            # in that direction, so set this component's value to 0.
            if l_loc == p_loc:
                list_vec[index] = 0
            else:
                # Otherwise, we take the product of self.movement_speed and duration,
                # negating it if we're intending to move in the other direction.
                list_vec[index] = (self.movement_speed * duration)
                if l_loc - p_loc < 0:
                    list_vec[index] = -list_vec[index]
            # At this point we have a movement vector reflecting the number of units
            # we want to move in a given direction for each component, so we just
            # add this number to our physical location to get our next location.
            list_vec[index] = p_loc + list_vec[index]
        return Coordinate(*list_vec)

    def move(self):
        """
        Moves an entity towards its logical location.
        :return: None
        """
        curr_time = time.time()
        new_location = self._new_movement_location(curr_time - self.last_update)

        # This block will evaluate if our new_location has reached or surpassed our target.
        # For both components, if we've reached or surpassed our target, then we're done moving.
        done_moving = False
        for (l_loc, n_loc, p_loc) in zip(self.logical_location, new_location, self.physical_location):
            p_distance = l_loc - p_loc
            n_distance = l_loc - n_loc
            done_moving = done_moving and (
                p_distance <= 0 <= n_distance or
                n_distance <= 0 <= p_distance
            )

        # Naively update our last_update time and our physical location.
        self.physical_location = new_location
        self.last_update = curr_time

        # If we're done moving, ensure our physical location matches our
        # logical location, reset movement state flags, and apply modifiers
        # that might be at the spot we've just arrived at.
        if done_moving:
            self.moving = False
            self.last_update = None
            self.physical_location = self.logical_location
            if self.movement_claimed_modifier:
                self.movement_claimed_modifier.modify(self)
            self.movement_claimed_modifier = None


class Player(Entity):
    identifier = "player"

    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.bombs = 1
        self.movement_speed = 1
        self.fire_distance = 3


class Bomb(Entity):
    identifier = "bomb"

    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)


class DestructibleWall(Entity):
    identifier = "destructible_wall"

    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)


class IndestructibleWall(Entity):
    identifier = "indestructible_wall"

    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)


class Modifier(Entity):
    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.solid = False

    def modify(self, entity):
        pass


class MovementModifier(Modifier):
    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)

    def modify(self, entity):
        entity.movement_speed += .1


class BombModifier(Modifier):
    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)

    def modify(self, entity):
        entity.bombs += 1


class FireModifier(Modifier):
    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)

    def modify(self, entity):
        entity.fire_distance += 1


class GameConfiguration(object):
    def __init__(self):
        pass
