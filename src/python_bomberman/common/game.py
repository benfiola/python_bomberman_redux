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
        # TODO: Remove conversion to list after development done - annoying workaround to pycharm unresolved attr errors when iterating over a set.
        return list(self._board[location.x][location.y])

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
        if not entity.is_moving and entity.bombs:
            new_bomb = entity.drop_bomb()
            self.add(new_bomb)
            new_bomb.set_to_detonate()

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
        for entity in self.all_entities():
            if entity.can_move and entity.is_moving:
                entity.update_move()
                if not entity.is_moving:
                    for other_entity in self.entities_at_location(entity.logical_location):
                        if other_entity.can_modify:
                            # TODO: for robustness, maybe add modifier logic to entity creation events as well.
                            other_entity.modify(entity)
                            other_entity.is_destroyed = True
            if entity.can_detonate and entity.is_detonating:
                entity.update_detonation()
                if entity.is_detonated:
                    entity.is_destroyed = True
                    entity.owner.bombs += 1
            # update last update time
            entity.last_update = time.time()
        for entity in [entity for entity in self.all_entities() if entity.can_destroy and entity.is_destroyed]:
            self.remove(entity)

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
            if entity and entity.can_collide:
                return True
        return False


@logger.create()
class Entity(object):
    def __init__(self, location, unique_id):
        if unique_id is None:
            unique_id = uuid4()
        self.logical_location = location
        self.physical_location = location
        self.unique_id = unique_id

        # random data some entities might have
        self.movement_speed = None
        self.bombs = 0
        self.bomb_duration = 0
        self.fire_distance = 0
        self.last_update = time.time()
        self.owner = None

        # definitions of actions entities can perform
        # and the state tied to them.
        self.can_modify = False
        self.can_collide = False
        self.can_move = False
        self.is_moving = False
        self.can_detonate = False
        self.is_detonating = False
        self.is_detonated = False
        self.can_destroy = False
        self.is_destroyed = False

    def set_to_move(self, location):
        """
        Sets up an entity to move.  
        :param location: Coordinate to move to
        :return: None
        """
        self.is_moving = True
        self.logical_location = location

    def set_to_detonate(self):
        self.is_detonating = True

    def drop_bomb(self):
        dropped_bomb = Bomb(self)
        self.bombs -= 1
        return dropped_bomb

    def update_detonation(self):
        curr_time = time.time()
        duration = curr_time - self.last_update
        self.bomb_duration -= duration
        if self.bomb_duration <= 0:
            self.is_detonated = True

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
                distance = 0
            else:
                # Otherwise, we take the product of self.movement_speed and duration,
                # negating it if we're intending to move in the other direction.
                distance = (self.movement_speed * duration)
                if l_loc - p_loc < 0:
                    distance = -list_vec[index]
            # At this point we have a movement vector reflecting the number of units
            # we want to move in a given direction for each component, so we just
            # add this number to our physical location to get our next location.
            new_coordinate = p_loc + distance
            list_vec.append(new_coordinate)
        return Coordinate(*list_vec)

    def update_move(self):
        """
        Moves an entity towards its logical location.
        :return: None
        """
        done_moving = True
        curr_time = time.time()

        # if this entity has no movement_speed, it's teleporting.
        # otherwise, apply movement over time to the entity.
        if not self.movement_speed:
            new_location = self.logical_location
        else:
            new_location = self._new_movement_location(curr_time - self.last_update)

            # This block will evaluate if our new_location has reached or surpassed our target.
            # For both components, if we've reached or surpassed our target, then we're done moving.
            for (l_loc, n_loc, p_loc) in zip(self.logical_location, new_location, self.physical_location):
                p_distance = l_loc - p_loc
                n_distance = l_loc - n_loc
                done_moving = done_moving and (
                    p_distance <= 0 <= n_distance or
                    n_distance <= 0 <= p_distance
                )

        # Naively update our physical location.
        self.physical_location = new_location

        # If we're done moving, ensure our physical location matches our
        # logical location, reset movement state flags, and apply modifiers
        # that might be at the spot we've just arrived at.
        if done_moving:
            self.is_moving = False
            self.physical_location = self.logical_location


class Player(Entity):
    identifier = "player"

    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.can_move = True
        self.can_destroy = True
        self.can_collide = True
        self.bombs = 1
        self.movement_speed = 1
        self.fire_distance = 3
        self.bomb_duration = 3


class Bomb(Entity):
    identifier = "bomb"

    def __init__(self, owner, unique_id=None):
        super().__init__(owner.logical_location, unique_id)
        self.can_detonate = True
        self.can_collide = True
        self.bomb_duration = owner.bomb_duration
        self.fire_distance = owner.fire_distance
        self.owner = owner


class DestructibleWall(Entity):
    identifier = "destructible_wall"

    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.can_destroy = True
        self.can_collide = True


class IndestructibleWall(Entity):
    identifier = "indestructible_wall"

    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.can_collide = True


class Modifier(Entity):
    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.can_modify = True
        self.can_destroy = True

    def modify(self, entity):
        pass


class MovementModifier(Modifier):
    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.amount = .1

    def modify(self, entity):
        entity.movement_speed += self.amount


class BombModifier(Modifier):
    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.amount = 1

    def modify(self, entity):
        entity.bombs += self.amount


class FireModifier(Modifier):
    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.amount = 1

    def modify(self, entity):
        entity.fire_distance += self.amount


class GameConfiguration(object):
    def __init__(self):
        pass
