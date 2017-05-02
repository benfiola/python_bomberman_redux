from python_bomberman.common.logging import logger
import json

@logger.create()
class Map(object):
    def __init__(self, width, height, name=None):
        self.name = name
        self.width = width
        self.height = height
        self._objects = [[None for _ in range(0, height)] for _ in range(0, width)]

    def objects(self):
        return [map_obj for row in self._objects for map_obj in row if map_obj is not None]

    def get_object(self, location):
        return self._objects[location.x][location.y]

    def add_object(self, to_add):
        self._objects[to_add.location.x][to_add.location.y] = to_add

    def remove_object(self, to_remove):
        self._objects[to_remove.location.x][to_remove.location.y] = None

    def save(self, filename):
        to_write = {
            "metadata": {
                "name": self.name,
                "width": self.width,
                "height": self.height
            },
            "objects": [
                {
                    "identifier": obj.identifier,
                    "location": obj.location
                } for obj in self.objects()]
        }
        with open(filename, 'w') as f:
            f.write(json.dumps(to_write))

    @classmethod
    def load(cls, filename):
        map_obj_classes = {map_cls.identifier: map_cls for map_cls in MapObject.__subclasses__()}
        with open(filename, 'r') as f:
            data = json.loads(f.read())
        to_return = cls(
            width=data["metadata"]["width"],
            height=data["metadata"]["height"],
            name=data["metadata"]["name"]
        )
        for map_obj_data in data["objects"]:
            if map_obj_data["identifier"] in map_obj_classes:
                map_obj_class = map_obj_classes[map_obj_data["identifier"]]
                to_return.add_object(
                    map_obj_class(
                        location=map_obj_data["location"]
                    )
                )
        return to_return


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

