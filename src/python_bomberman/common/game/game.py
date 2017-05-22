from python_bomberman.common.logging import logger
from python_bomberman.common.game.board import Board
from python_bomberman.common.utils import Coordinate
import python_bomberman.common.game.entities as entities
import time

@logger.create()
class Game(object):
    def __init__(self, game_map):
        self._board = Board(
            height=game_map.height,
            width=game_map.width
        )
        self._entities = {}

        for entity in self._convert_map_objects(game_map.all_objects()):
            self.add(entity)

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
        self._board.add(entity)
        self._entities[entity.unique_id] = entity

    def remove(self, entity):
        """
        Will remove an entity from both the entity map as well as the gameboard.
        :param entity: Entity to be removed
        :return: None
        """
        self._board.remove(entity)
        self._entities.pop(entity.unique_id)

    def drop_bomb(self, entity):
        if not entity.is_moving and entity.bombs:
            bomb = entities.Bomb(
                location=entity.logical_location,
                owner=entity
            )
            entity.bombs -= 1
            self.add(bomb)
            bomb.is_detonating = True

    def move(self, entity, location):
        """
        Sets up an entity to be further processed for movement given a location.
        :param entity: Entity that needs to be moved
        :param location: desired Coordinate to move Entity to.
        :return: 
        """
        if not isinstance(self._board.get_space(location).entity, entities.Collideable):
            self._board.remove(entity)
            entity.is_moving = True
            entity.logical_location = location
            self._board.add(entity)

    def process(self):
        """
        Processes the gameboard and updates entities currently undergoing time-based modification.
        :return: None
        """
        for entity in self._all_entities():
            if isinstance(entity, entities.Movable) and entity.is_moving:
                entity.move_update()
                if not entity.is_moving:
                    board_space = self._board.get_space(entity.logical_location)
                    if board_space.modifier:
                        modifier = board_space.modifier
                        modifier.modify(entity)
                        modifier.is_destroyed = True
            if isinstance(entity, entities.Detonatable) and entity.is_detonating:
                entity.detonate_update()
                if entity.is_detonated:
                    # flag our bomb as destroyed, give a bomb back to the owner
                    entity.is_destroyed = True

                    if isinstance(entity, entities.Bomb):
                        entity.owner.bombs += 1

                    # go in all directions, destroying everything until we run out of locations or have to stop.
                    # TODO: check and ensure that locations are valid.
                    for coordinate in self._get_detonation_locations(entity.logical_location, entity.fire_distance):
                        board_space = self._board.get_space(coordinate)
                        if board_space.modifier:
                            board_space.modifier.is_destroyed = True
                        if board_space.entity:
                            board_space.entity.is_destroyed = True
                        fire = entities.Fire(coordinate)
                        fire.is_burning = True
                        self.add(fire)
            if isinstance(entity, entities.Burnable) and entity.is_burning:
                entity.burn_update()
                if not entity.is_burning:
                    entity.is_destroyed = True

            # update last update time
            entity.last_update = time.time()

        # now clean up anything that's been destroyed
        for entity in [entity for entity in self._all_entities() if isinstance(entity, entities.Destroyable) and entity.is_destroyed]:
            self.remove(entity)

    def _get_detonation_locations(self, location, fire_distance):
        to_return = [location]

        # consider each direction a lambda that takes a distance argument
        # and modifies the passed in location.
        for direction in [
            lambda dist: Coordinate(location.x+dist, location.y),
            lambda dist: Coordinate(location.x-dist, location.y),
            lambda dist: Coordinate(location.x, location.y+dist),
            lambda dist: Coordinate(location.x, location.y-dist)
        ]:
            # for each distance lambda, lets iterate over the range of the
            # bomb explosion
            for distance in range(1, fire_distance):
                # for each newly generated coordinate, lets
                # see if we've encountered something that we can't
                # destroy.  if so, we stop here, otherwise, we continue
                # adding locations to our list we're going to return.
                new_location = direction(distance)
                board_space = self._board.get_space(new_location)
                if not isinstance(board_space.entity, entities.Destroyable):
                    break
                to_return.append(new_location)
        return to_return

    @classmethod
    def _entity_class_helper(cls, _class, to_return):
        for _subclass in _class.__subclasses__():
            if hasattr(_subclass, "identifier"):
                to_return[_subclass.identifier] = _subclass
            cls._entity_class_helper(_subclass, to_return)

    @classmethod
    def _convert_map_objects(cls, map_objs):
        entity_classes = {}
        cls._entity_class_helper(entities.Entity, entity_classes)
        return [
            entity_classes[map_obj.identifier](
                location=map_obj.location
            ) for map_obj in map_objs if map_obj.identifier in entity_classes
        ]

    def _all_entities(self):
        return list(self._entities.values())
