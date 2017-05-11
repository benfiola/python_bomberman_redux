from python_bomberman.common.logging import logger
from uuid import uuid4

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
        entity_classes = {cls.identifier: cls for cls in Entity.__subclasses__()}
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

    def add_entity(self, entity):
        self._entities[entity.unique_id] = entity
        self._board[entity.location.x][entity.location.y] = entity

    def remove_entity(self, entity):
        self._entities.pop(entity.unique_id)
        self._board[entity.location.x][entity.location.y] = None


class Entity(object):
    def __init__(self, location, unique_id):
        if unique_id is None:
            unique_id = uuid4()
        self.location = location
        self.unique_id = unique_id


class Player(Entity):
    identifier = "player"

    def __init__(self, location, unique_id=None):
        super().__init__(location, unique_id)
        self.bombs = 1
        self.movement_speed = 1


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


class GameConfiguration(object):
    def __init__(self):
        pass
