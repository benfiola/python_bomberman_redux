from python_bomberman.common.game.board import Board
from python_bomberman.common.game.entity_map import EntityMap
from python_bomberman.common.game.exceptions import GameException
from python_bomberman.common.game.tasks import TaskManager
import python_bomberman.common.game.entities as entities


class Game:
    def __init__(self, game_map):
        self.board = Board(dimensions=game_map.dimensions)
        self.entities = EntityMap()
        self.tasks = TaskManager(self)

        map_obj_cls = {}
        to_check = entities.Entity.__subclasses__()
        while to_check:
            cls = to_check.pop()
            to_check.extend(cls.__subclasses__())
            if hasattr(cls, "identifier"):
                map_obj_cls[cls.identifier] = cls
        for map_obj in game_map.all_objects():
            if map_obj.identifier in map_obj_cls:
                self.add(map_obj_cls[map_obj.identifier](location=map_obj.location))

    def add(self, entity):
        self.board.add(entity)
        self.entities.add(entity)

        space = self.board.get(entity.logical_location)

        if space.has_fire() and entity.can_be_destroyed:
            entity.destroyed = True
        if space.has_modifier() and entity.can_be_modified:
            space.modifier.modify(entity)
            space.modifier.destroyed = True

    def remove(self, entity):
        self.board.remove(entity)
        self.entities.remove(entity)

    def drop_bomb(self, entity):
        if not entity.can_drop_bombs:
            raise GameException.entity_incapable_of_performing_action(entity, "drop bomb")

        space = self.board.get(entity.logical_location)

        if entity.destroyed:
            return
        if entity.moving:
            return
        if not entity.bombs:
            return
        if space.has_bomb():
            return

        bomb = entities.Bomb(
            location=entity.logical_location,
            radius=entity.bomb_radius
        )
        entity.bombs -= 1
        self.tasks.register_detonation_task(bomb, entity)

    def move(self, entity, direction, num_spaces):
        if not entity.can_move:
            raise GameException.entity_incapable_of_performing_action(entity, "move")
        if entity.destroyed:
            return
        self.tasks.register_movement_task(entity, direction, num_spaces)

    def process(self):
        # process the tasks that are active
        self.tasks.run()

        # remove any destroyed entities
        for entity in self.entities.destroyed_entities():
            self.remove(entity)
