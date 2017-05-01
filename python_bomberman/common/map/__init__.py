from python_bomberman.common.logging import logger


@logger.create()
class Map(object):
    def __init__(self, width, height, name=None):
        self.name = name
        self.width = width
        self.height = height
        self.objects = [[None for _ in range(0, height)] for _ in range(0, width)]

    def objects(self):
        return [map_obj for row in self.objects for map_obj in row]

    def get_object(self, location):
        return self.objects[location.x()][location.y()]

    def add_object(self, to_add):
        self.objects[to_add.location.x()][to_add.location.y()] = to_add

    def remove_object(self, to_remove):
        self.objects[to_remove.location.x()][to_remove.location.y()] = None


class MapObject(object):
    def __init__(self, location):
        self.location = location


class Player(MapObject):
    identifier = "player"

    def __init__(self, location):
        super().__init__(location)


class DestructibleWall(MapObject):
    identifier = "destructible_wall"

    def __init__(self, location):
        super().__init__(location)


class IndestructibleWall(MapObject):
    identifier = "indestructible_wall"

    def __init__(self, location):
        super().__init__(location)

