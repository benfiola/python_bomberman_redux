from python_bomberman.common.logging import logger
from python_bomberman.common.utils import Coordinate
from uuid import uuid4
import time
import math


@logger.create()
class Game(object):
    def __init__(self, game_map, configuration):
        self.configuration = configuration
        self._board = [[set() for _ in range(0, game_map.height)] for _ in range(0, game_map.width)]
        self._entities = {}

        for entity in self._convert_map_objects(game_map.all_objects()):
            self.add(entity)

    @staticmethod
    def _convert_map_objects(map_objs):
        entity_classes = {cls.identifier: cls for cls in Entity.__subclasses__() if hasattr(cls, "identifier")}
        return [
            entity_classes[map_obj.identifier](
                location=map_obj.location
            ) for map_obj in map_objs if map_obj.identifier in entity_classes
        ]

    def all_entities(self):
        return self._entities.values()

    def entities_at_location(self, location):
        return self._board[location.x][location.y]

    def entity_by_id(self, unique_id):
        if unique_id in self._entities:
            return self._entities[unique_id]
        return None

    def add(self, entity):
        """
        Will add an entity to both the entity map as well as the gameboard.
        :param entity: Entity to be added
        :return: None
        """
        self._add_to_entity_map(entity)
        self._add_to_board(entity)

    def remove(self, entity):
        """
        Will remove an entity from both the entity map as well as the gameboard.
        :param entity: Entity to be removed
        :return: None
        """
        self._remove_from_board(entity)
        self._remove_from_entity_map(entity)

    def drop_bomb(self, entity):
        if not entity.moving and entity.bombs:
            entity.bombs -= 1
            new_bomb = Bomb(entity.logical_location, entity.bomb_duration, entity.fire_distance)
            self.add(new_bomb)
            new_bomb.set_to_explode()

    def move(self, entity, location):
        """
        Sets up an entity to be further processed for movement given a location.
        :param entity: Entity that needs to be moved
        :param location: desired Coordinate to move Entity to.
        :return: 
        """
        if not self._has_collision(location):
            self._remove_from_board(entity)
            entity.set_to_move(location)
            self._add_to_board(entity)

    def process(self):
        """
        Processes the gameboard and updates entities currently undergoing time-based modification.
        :return: None
        """
        for entity in self.get_entities():
            if entity.moving:
                entity.move()
                if not entity.moving:
                    for other_entity in self.entities_at_location(entity.logical_location):
                        if other_entity.modifier:
                            other_entity.modify(entity)
                            self.remove(other_entity)
            if entity.armed:
                entity.explodable_count_down()
                if entity.explodable_detonated:
                    # TODO: Handle detonation
                    pass

    def _remove_from_board(self, entity):
        self._board[entity.logical_location.x][entity.logical_location.y].remove(entity)

    def _remove_from_entity_map(self, entity):
        self._entities.pop(entity.unique_id)

    def _add_to_board(self, entity):
        self._board[entity.logical_location.x][entity.logical_location.y].add(entity)

    def _add_to_entity_map(self, entity):
        self._entities[entity.unique_id] = entity

    def _has_collision(self, location):
        """
        Checks to see if a given Coordinate is occupied by a solid entity.
        :param location: Location where collision check is performed
        :return: bool indicating whether spot is occupied
        """
        for entity in self.entities_at_location(location):
            if entity and entity.solid:
                return True
        return False


class Entity(object):
    def __init__(self, location, unique_id):
        if unique_id is None:
            unique_id = uuid4()
        self.logical_location = location
        self.physical_location = location
        self.unique_id = unique_id

        # state related attributes
        # TODO: Figure out how to do this such that we don't have infinity attributes in our base class.
        self.moving = False
        self.movement_speed = None
        self.movement_last_update = None
        self.armed = False
        self.explodable_detonated = False
        self.explodable_last_update = None
        self.explodable_countdown = None

        # properties
        self.solid = True
        self.modifier = False

    def set_to_move(self, location):
        """
        Sets up an entity to move.  
        :param location: Coordinate to move to
        :return: None
        """
        self.moving = True
        self.movement_last_update = time.time()
        self.logical_location = location

    def set_to_explode(self):
        self.armed = True
        self.explodable_last_update = time.time()

    def explodable_count_down(self):
        curr_time = time.time()
        duration = curr_time - self.explodable_last_update
        self.explodable_countdown -= duration
        self.explodable_last_update = curr_time
        if self.explodable_countdown <= 0:
            self.explodable_detonated = True

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
        done_moving = False
        curr_time = time.time()

        # if this entity has no movement_speed, it's teleporting.
        # otherwise, apply movement over time to the entity.
        if not self.movement_speed:
            new_location = self.logical_location
            done_moving = True
        else:
            new_location = self._new_movement_location(curr_time - self.movement_last_update)

            # This block will evaluate if our new_location has reached or surpassed our target.
            # For both components, if we've reached or surpassed our target, then we're done moving.
            for (l_loc, n_loc, p_loc) in zip(self.logical_location, new_location, self.physical_location):
                p_distance = l_loc - p_loc
                n_distance = l_loc - n_loc
                done_moving = done_moving and (
                    p_distance <= 0 <= n_distance or
                    n_distance <= 0 <= p_distance
                )

        # Naively update our last_update time and our physical location.
        self.physical_location = new_location
        self.movement_last_update = curr_time

        # If we're done moving, ensure our physical location matches our
        # logical location, reset movement state flags, and apply modifiers
        # that might be at the spot we've just arrived at.
        if done_moving:
            self.moving = False
            self.movement_last_update = None
            self.physical_location = self.logical_location


class Player(Entity):
    identifier = "player"

    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.bombs = 1
        self.movement_speed = 1
        self.fire_distance = 3
        self.bomb_duration = 3


class Bomb(Entity):
    identifier = "bomb"

    def __init__(self, location, countdown, fire_distance, unique_id=None):
        super().__init__(location, unique_id)
        self.explodable_countdown = countdown
        self.fire_distance = fire_distance


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
