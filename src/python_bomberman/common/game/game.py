from python_bomberman.common.game.board import Board
from python_bomberman.common.game.entity_map import EntityMap
from python_bomberman.common.game.exceptions import GameException
import python_bomberman.common.game.entities as entities
import time


class Game:
    def __init__(self, game_map):
        self._board = Board(dimensions=game_map.dimensions)
        self._entities = EntityMap()
        self._tasks = []

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
        self._board.add(entity)
        self._entities.add(entity)

    def remove(self, entity):
        self._board.remove(entity)
        self._entities.remove(entity)

    def drop_bomb(self, entity):
        if not entity.can_drop_bombs:
            raise GameException.entity_incapable_of_performing_action(entity, "drop bomb")
        if not entity.destroyed and not entity.moving and entity.bombs and not self._board.get(entity.logical_location).has_bomb():
            # TODO: drop a bomb and manage its detonation using a TimedTask
            pass

    def move(self, entity, direction, num_spaces):
        if not entity.can_move:
            raise GameException.entity_incapable_of_performing_action(entity, "move")
        if not entity.destroyed:
            # TODO: move entity using TimedTask (but how do we interrupt previous move tasks for this entity)
            pass

    def process(self):
        # process the tasks that are active
        for task in list(self._tasks):
            task.run()
            if task.done:
                self._tasks.remove(task)
        # remove any destroyed entities
        for entity in [entity for entity in self._entities.all_entities() if entity.destroyed]:
            self.remove(entity)


class TimedTask(object):
    def __init__(self, game):
        self.game = game

        self.last_update = None
        self.started = False
        self.done = False

    def on_start(self):
        # if there's setup required prior to the task running for the first time,
        # this is the hook to use!
        pass

    def needs_removal(self):
        # if we prematurely need to remove the task because the entities involved in the task
        # should no longer exist, then we leverage this hook to prematurely kill the task
        pass

    def run(self):
        if self.needs_removal():
            self.done = True
            return

        if not self.started:
            self.on_start()
        self.process()
        if self.done:
            self.on_finish()

    def process(self):
        # this is the method that runs until it decides it's finished by setting the
        # self.done flag to True
        pass

    def on_finish(self):
        # if we need to trigger other behaviors upon this task finishing, this is the
        # hook to use!
        pass


class MovementTask(TimedTask):
    def __init__(self, game, entity):
        super().__init__(game)
        self.game = game
        self.entity = entity

    def needs_removal(self):
        pass

    def process(self):
        pass

    def on_finish(self):
        pass


class DetonationTask(TimedTask):
    def __init__(self, game, entity):
        super().__init__(game)
        self.game = game
        self.entity = entity

    def process(self):
        pass

    def on_finish(self):
        pass


class BurningTask(TimedTask):
    def __init__(self, game):
        super().__init__(game)
        pass

    def process(self):
        pass

    def on_finish(self):
        pass
