import time
from python_bomberman.common.game.constants import MovementDirection
import python_bomberman.common.utils as utils
import python_bomberman.common.game.entities as entities


class TaskManager(object):
    def __init__(self, game):
        self.game = game
        self._tasks = {}

    def _register_task(self, task):
        entity = task.entity

        # removes a task of the same class that might exist already for this entity
        # (only one of each task for any entity at any given time)
        self._tasks[entity.unique_id] = list(filter(
            lambda val: val.__class__ != task.__class__,
            self._tasks.get(entity.unique_id, [])
        ))

        self._tasks[entity.unique_id].append(task)

    def unregister_task(self, task):
        entity = task.entity

        # remove the task being unregistered
        self._tasks[entity.unique_id] = list(filter(
            lambda val: val != task,
            self._tasks.get(entity.unique_id, [])
        ))

        # remove the key if it has no active tasks
        if not self._tasks[entity.unique_id]:
            self._tasks.pop(entity.unique_id)

    def register_movement_task(self, entity, direction, distance):
        to_return = MovementTask(self.game, entity, direction, distance)
        self._register_task(to_return)
        return to_return

    def register_detonation_task(self, entity, bomb_owner):
        to_return = DetonationTask(self.game, entity, bomb_owner)
        self._register_task(to_return)
        return to_return

    def register_burning_task(self, entity):
        to_return = BurningTask(self.game, entity)
        self._register_task(to_return)
        return to_return

    def run(self):
        for task in self._tasks.values():
            task.run()


class TimedTask(object):
    def __init__(self, game, entity):
        self.game = game
        self.board = game.board
        self.task_manager = game.tasks
        self.entity = entity
        self.last_update = None
        self.started = False
        self.done = False

    def _on_start(self):
        self.started = True
        self.last_update = time.time()

    def _on_finish(self):
        self.task_manager.unregister_task(self)

    def run(self):
        if self.needs_removal():
            self.done = True
        if not self.started:
            self._on_start()
            self.on_start()
        if not self.done:
            self.process()
            self.last_update = time.time()
            if self.done:
                self._on_finish()
                self.on_finish()

    def on_start(self):
        # use this hook to do any setup prior to starting the timed task.
        pass

    def needs_removal(self):
        # if we prematurely need to remove the task because the entities involved in the task
        # should no longer exist, then we leverage this hook to prematurely kill the task
        return self.entity.destroyed

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

    def on_start(self):
        space = self.board.get(self.entity.logical_location, self.direction, 1)
        if not space.occupied(self.entity):
            self.entity.moving = True
            self.entity.logical_location = space.location
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

        space = self.board.get(self.entity.logical_location)

        if self.entity.can_be_modified and space.has_modifier():
            space.modifier.modify(self.entity)
            space.modifier.destroyed = True
        if self.entity.can_destroy and space.has_fire():
            self.entity.destroyed = True

        if self.distance > 1:
            self.task_manager.register_movement_task(self.entity, self.direction, self.distance - 1)

    def _new_physical_location(self, duration):
        # add distance traveled to each coordinate
        new_loc = [coord + dist for coord, dist in zip(self.entity.physical_location, self._distance_moved(duration))]

        # no trendy shorthand for this bad boy - if we're going
        # off the edge of the board, move it to the other side.
        for index, (coord, dimension) in enumerate(zip(new_loc, self.board.dimensions)):
            if coord < -0.5:
                new_loc[index] += dimension
            elif coord > (dimension - .5):
                new_loc[index] -= dimension

        return utils.Coordinate(*new_loc)

    def _distance_moved(self, duration):
        distance = self.entity.movement_speed * duration
        distance_map = {
            MovementDirection.LEFT: utils.Coordinate(-distance, 0.0),
            MovementDirection.RIGHT: utils.Coordinate(distance, 0.0),
            MovementDirection.UP: utils.Coordinate(0.0, -distance),
            MovementDirection.DOWN: utils.Coordinate(0.0, distance)
        }
        return distance_map.get(self.direction, utils.Coordinate(0.0, 0.0))

    def _done_moving(self, old_loc, new_loc, target):
        finished_map = {
            MovementDirection.LEFT: new_loc.x <= target.x <= old_loc.x,
            MovementDirection.RIGHT: old_loc.x <= target.x <= new_loc.x,
            MovementDirection.UP: new_loc.y <= target.y <= old_loc.y,
            MovementDirection.DOWN: old_loc.y <= target.y <= new_loc.y
        }
        return finished_map.get(self.direction, True)


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

        self.bomb_owner.bombs += 1

        for space in self.board.blast_radius(self.entity.logical_location, self.entity.radius):
            space.destroy_all()
            fire = self.game.add(entities.Fire(space.location))
            self.task_manager.register_burning_task(fire)


class BurningTask(TimedTask):
    def __init__(self, game, entity):
        super().__init__(game, entity)

    def on_start(self):
        self.entity.burning = True

    def process(self):
        self.entity.duration -= (time.time() - self.last_update)
        self.done = (self.entity.duration <= 0)

    def on_finish(self):
        self.entity.burning = False
        self.entity.destroyed = True
