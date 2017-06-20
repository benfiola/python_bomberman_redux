from python_bomberman.common.game.board import Board
from python_bomberman.common.game.entity_map import EntityMap
from python_bomberman.common.game.exceptions import GameException
from python_bomberman.common.game.tasks import MovementTask, DetonationTask
import python_bomberman.common.game.entities as entities


class Game:
    def __init__(self, game_map):
        self._board = Board(dimensions=game_map.dimensions)
        self._entities = EntityMap()
        self._tasks = {}

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

    def register_task(self, task):
        entity = task.entity

        # removes a task of the same class that might exist already for this entity
        # (only one of each task for any entity at any given time)
        self._tasks[entity.unique_id] = filter(
            lambda val: val.__class__ != task.__class__,
            self._tasks.get(entity.unique_id, [])
        )

        self._tasks[entity.unique_id].append(task)

    def unregister_task(self, task):
        entity = task.entity

        # remove the task being unregistered
        self._tasks[entity.unique_id] = filter(
            lambda val: val != task,
            self._tasks.get(entity.unique_id, [])
        )

        # remove the key if it has no active tasks
        if not self._tasks[entity.unique_id]:
            self._tasks.pop(entity.unique_id)

    def add(self, entity):
        self._board.add(entity)
        self._entities.add(entity)

        loc = entity.logical_location
        space = self._board.get(loc)

        if space.has_fire() and entity.can_be_destroyed:
            entity.destroyed = True
        if space.has_modifier() and entity.can_be_modified:
            space.modifier.modify(entity)
            space.modifier.destroyed = True

    def remove(self, entity):
        self._board.remove(entity)
        self._entities.remove(entity)

    def drop_bomb(self, entity):
        if not entity.can_drop_bombs:
            raise GameException.entity_incapable_of_performing_action(entity, "drop bomb")

        if entity.destroyed:
            return
        if entity.moving:
            return
        if not entity.bombs:
            return
        if self._board.get(entity.logical_location).has_bomb():
            return

        bomb = entities.Bomb(
            location=entity.logical_location,
            radius=entity.bomb_radius
        )
        entity.bombs -= 1
        self.register_task(DetonationTask(self, bomb, entity))

    def move(self, entity, direction, num_spaces):
        if not entity.can_move:
            raise GameException.entity_incapable_of_performing_action(entity, "move")
        if entity.destroyed:
            return
        self.register_task(MovementTask(self, entity, direction, num_spaces))

    def process(self):
        # process the tasks that are active
        for task in self._tasks.values():
            task.run()

        # remove any destroyed entities
        for entity in [entity for entity in self._entities.all_entities() if entity.destroyed]:
            self.remove(entity)
