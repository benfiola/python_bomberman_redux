from python_bomberman.common.game.board import Board
from python_bomberman.common.game.entity_map import EntityMap
from python_bomberman.common.game.exceptions import GameException
from python_bomberman.common.game.movement_direction import MovementDirection
import python_bomberman.common.game.entities as entities
import python_bomberman.common.utils as utils
import time


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
        self._tasks[entity.unique_id] = filter(
            lambda val: val.__class__ != task.__class__,
            self._tasks.get(entity.unique_id, [])
        )
        self._tasks[entity.unique_id].append(task)

    def unregister_task(self, task):
        entity = task.entity
        self._tasks[entity.unique_id] = filter(
            lambda val: val != task,
            self._tasks.get(entity.unique_id, [])
        )
        if not self._tasks[entity.unique_id]:
            self._tasks[entity.unique_id] = None

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


class TimedTask(object):
    def __init__(self, game, entity):
        self.game = game
        self.entity = entity
        self.last_update = None
        self.started = False
        self.done = False

    def _on_start(self):
        self.started = True
        self.last_update = time.time()

    def _on_finish(self):
        self.game.unregister_task(self)

    def run(self):
        if self.needs_removal():
            self.done = True
        if not self.started:
            self._on_start()
            self.on_start()
        if not self.done:
            self.process()
            self.last_update = time.time()
        else:
            self._on_finish()
            self.on_finish()

    def on_start(self):
        # use this hook to do any setup prior to starting the timed task.
        pass

    def needs_removal(self):
        # if we prematurely need to remove the task because the entities involved in the task
        # should no longer exist, then we leverage this hook to prematurely kill the task
        return False

    def process(self):
        # this is the method that runs until it decides it's finished by setting the
        # self.done flag to True
        pass

    def on_finish(self):
        # use this hook to do any post-work after finishing the timed task
        pass


class MovementTask(TimedTask):
    def __init__(self, game, entity, direction, distance):
        super().__init__(game, entity)
        self.direction = direction
        self.distance = distance

    def needs_removal(self):
        return self.entity.destroyed

    def on_start(self):
        new_location = self.game._board.relative_location(self.entity.logical_location, self.direction, 1)
        if not self.game._board.get(new_location).occupied(self.entity):
            self.entity.moving = True
            self.entity.logical_location = new_location
        else:
            self.done = True

    def process(self):
        entity = self.entity
        duration = (time.time() - self.last_update)

        old_loc = entity.physical_location
        new_loc = self._new_physical_location(duration)

        entity.physical_location = new_loc
        self.done = self._done_moving(old_loc, new_loc, entity.logical_location)

    def on_finish(self):
        self.entity.moving = False
        self.entity.physical_location = self.entity.logical_location

        space = self.game._board.get(self.entity.logical_location)
        if self.entity.can_be_modified and space.has_modifier():
            space.modifier.modify(self.entity)
            space.modifier.destroyed = True
        if self.entity.can_be_destroyed and space.has_fire():
            self.entity.destroyed = True

        if not self.entity.destroyed and self.distance > 0:
            self.game.register_task(self.entity, self.direction, self.distance - 1)

    def _done_moving(self, old_loc, new_loc, target):
        finished_map = {
            MovementDirection.LEFT: new_loc[0] <= target[0] <= old_loc[0],
            MovementDirection.RIGHT: old_loc[0] <= target[0] <= new_loc[0],
            MovementDirection.UP: new_loc[1] <= target[1] <= old_loc[1],
            MovementDirection.DOWN: old_loc[1] <= target[1] <= new_loc[1]
        }
        return finished_map.get(self.direction, True)

    def _new_physical_location(self, duration):
        entity = self.entity

        # get starting point
        coordinates = [
            *entity.physical_location
        ]

        # get distance moved
        distance = entity.movement_speed * duration
        distance_map = {
            MovementDirection.LEFT: [-distance, 0],
            MovementDirection.RIGHT: [distance, 0],
            MovementDirection.UP: [0, -distance],
            MovementDirection.DOWN: [0, distance]
        }
        distances = distance_map.get(self.direction, [0, 0])

        # calculate new coordinate, moving entity past end of table onto other side if needed.
        for index, (coordinate, distance, dimension) in enumerate(zip(coordinates, distances, self.game._board.dimensions)):
            coordinates[index] = coordinate + distance
            if coordinates[index] < -0.5:
                coordinates[index] += dimension
            elif coordinates[index] > (dimension - .5):
                coordinates[index] -= dimension

        return utils.Coordinate(*coordinates)


class DetonationTask(TimedTask):
    def __init__(self, game, entity, bomb_owner):
        super().__init__(game, entity)
        self.bomb_owner = bomb_owner

    def on_start(self):
        self.entity.detonating = True

    def process(self):
        self.entity.duration -= (time.time() - self.last_update)
        self.done = (self.entity.duration <= 0)

    def on_finish(self):
        self.entity.detonating = False
        self.entity.destroyed = True
        if not self.bomb_owner.destroyed:
            self.bomb_owner.bombs += 1
        for location in self.game._board.blast_radius(self.entity.logical_location, self.entity.radius):
            fire = self.game.add(entities.Fire(location))
            self.game.register_task(BurningTask(self.game, fire))
            self.game._board.get(location).destroy_all()



class BurningTask(TimedTask):
    def __init__(self, game, entity):
        super().__init__(game, entity)
        self.duration = entity.duration

    def on_start(self):
        self.entity.burning = True

    def needs_removal(self):
        return self.entity.destroyed

    def process(self):
        self.entity.duration -= (time.time() - self.last_update)
        self.done = (self.entity.duration <= 0)

    def on_finish(self):
        self.entity.burning = False
        self.entity.destroyed = True
