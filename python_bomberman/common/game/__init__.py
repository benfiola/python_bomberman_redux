from python_bomberman.common.logging import logger
from uuid import uuid4

@logger.create()
class Game(object):
    def __init__(self, map, configuration):
        self.configuration = configuration
        self.map = map
        self.board = [[None for _ in range(0, map.height)] for _ in range(0, map.width)]
        self.entities = {}
        for map_obj in self.map.objects():
            to_add = self._convert_map_obj(map_obj)
            if to_add:
                self.add_entity(to_add)

    def get_entity(self, location=None, identifier=None):
        if location:
            return self.board[location.x()][location.y()]
        if identifier:
            return self.entities[identifier]

    def add_entity(self, entity):
        self.entities[entity.identifier] = entity

    def remove_entity(self, entity):
        self.entities.pop(entity.identifier)
        self.board[entity.location.x()][entity.location.y()] = None

    def _convert_map_obj(self, map_obj):
        if map_obj.identifier == "player":
            return Player(map_obj.location)
        elif map_obj.identifier == "destructible_wall":
            return DestructibleWall(map_obj.location)
        elif map_obj.identifier == "indestructible_wall":
            return IndestructibleWall(map_obj.location)

class Entity(object):
    def __init__(self, location, identifier=uuid4()):
        self.location = location
        self.identifier = identifier

class Player(Entity):
    def __init__(self, location, identifier=uuid4()):
        super().__init__(location, identifier)

class Bomb(Entity):
    def __init__(self, location, identifier=uuid4()):
        super().__init__(location, identifier)

class DestructibleWall(Entity):
    def __init__(self, location, identifier=uuid4()):
        super().__init__(location, identifier)

class IndestructibleWall(Entity)
    def __init__(self, location, identifier=uuid4()):
        super().__init__(location, identifier)
