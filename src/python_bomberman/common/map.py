from python_bomberman.common.logging import logger
from python_bomberman.common.utils import Coordinate
import json

@logger.create()
class Map(object):
    def __init__(self, dimensions, name=None, objects=None):
        self.name = name
        self.dimensions = dimensions
        self._objects = [[None for _ in range(0, dimensions.y)] for _ in range(0, dimensions.x)]

        if objects:
            for obj in objects:
                self.add(obj)

    def all_objects(self):
        return [map_obj for row in self._objects for map_obj in row if map_obj is not None]

    def object_at_location(self, location):
        return self._objects[location.x][location.y]

    def add(self, to_add):
        self._objects[to_add.location.x][to_add.location.y] = to_add

    def remove(self, to_remove):
        self._objects[to_remove.location.x][to_remove.location.y] = None

    def save(self, filename):
        to_write = {
            "metadata": {
                "name": self.name,
                "dimensions": self.dimensions
            },
            "objects": [
                {
                    "identifier": obj.identifier,
                    "location": obj.location
                } for obj in self.all_objects()]
        }
        with open(filename, 'w') as f:
            f.write(json.dumps(to_write))

    @classmethod
    def load(cls, filename):
        # find all map object definitions
        obj_classes = {map_cls.identifier: map_cls for map_cls in MapObject.__subclasses__() if hasattr(map_cls, "identifier")}

        # read the json data from a map file
        with open(filename, 'r') as f:
            data = json.loads(f.read())

        # create our map objects
        # this requires us to do a lookup on the MapObject subclasses we know of, finding the class
        # this data object pertains to and invoking its constructor on the data we have.
        objs = [
            obj_classes[obj["identifier"]](
                location=Coordinate(*obj["location"])
            ) for obj in data["objects"] if obj["identifier"] in obj_classes
        ]
        dimensions = Coordinate(**data["metadata"].pop("dimensions"))
        return cls(
            dimensions,
            **data["metadata"],
            objects=objs
        )

    def __eq__(self, other):
        try:
            return (
                self.name == other.name and
                self.dimensions == other.dimensions and
                self.all_objects() == other.all_objects()
            )
        except AttributeError:
            return False


class MapObject(object):
    identifier = None

    def __init__(self, location):
        self.location = location

    def __eq__(self, other):
        try:
            return (
                self.identifier == other.identifier and
                self.location == other.location
            )
        except AttributeError:
            return False


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

