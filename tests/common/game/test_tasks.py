import pytest
from python_bomberman.common.game.game import Game
from python_bomberman.common.game.tasks import TaskManager, BurningTask, MovementTask, DetonationTask
from python_bomberman.common.game.entities import Bomb, Player, Fire
from python_bomberman.common.game.constants import MovementDirection
from python_bomberman.common.map import Map
from python_bomberman.common.utils import Coordinate
import time


@pytest.fixture
def entity_location():
    return Coordinate(2, 2)


@pytest.fixture
def game_map():
    return Map(
        dimensions=Coordinate(5, 5)
    )


@pytest.fixture
def game(game_map):
    return Game(game_map=game_map)


@pytest.fixture
def bomb(entity_location):
    return Bomb(location=entity_location, duration=2, radius=3)


@pytest.fixture
def player(entity_location):
    return Player(location=entity_location)


@pytest.fixture
def fire(entity_location):
    return Fire(location=entity_location)


@pytest.fixture
def task_manager(game):
    return TaskManager(game)


class TestTaskManagerSuite:
    def test_init(self, task_manager, game):
        assert task_manager._tasks is not None
        assert task_manager.game == game

    def test_register_movement_task(self, task_manager, player):
        task_1 = task_manager.register_movement_task(player, direction=MovementDirection.UP, distance=2)
        task_2 = task_manager.register_movement_task(player, direction=MovementDirection.DOWN, distance=1)
        task_list = task_manager._tasks.get(player.unique_id, None)
        assert task_list is not None and task_2 in task_list and task_1 not in task_list

    def test_register_burning_task(self, task_manager, fire):
        task_1 = task_manager.register_burning_task(fire)
        task_2 = task_manager.register_burning_task(fire)
        task_list = task_manager._tasks.get(fire.unique_id, None)
        assert task_list is not None and task_2 in task_list and task_1 not in task_list

    def test_register_detonation_task(self, task_manager, bomb, player):
        task_1 = task_manager.register_detonation_task(bomb, player)
        task_2 = task_manager.register_detonation_task(bomb, player)
        task_list = task_manager._tasks.get(bomb.unique_id, None)
        assert task_list is not None and task_2 in task_list and task_1 not in task_list

    def test_add_multiple(self, task_manager, player, bomb):
        movement = task_manager.register_movement_task(bomb, direction=MovementDirection.UP, distance=2)
        detonation = task_manager.register_detonation_task(bomb, player)
        task_list = task_manager._tasks.get(bomb.unique_id, None)
        assert task_list is not None and movement in task_list and detonation in task_list


class TestMovementTaskSuite:
    @pytest.fixture
    def task(self, game, player):
        game.add(player)
        return MovementTask(game, player, direction=MovementDirection.UP, distance=2)

    def test_init(self, task, game, player):
        assert task.game == game
        assert task.task_manager == game.tasks
        assert task.board == game.board
        assert task.entity == player
        assert task.last_update is None
        assert task.started is False
        assert task.done is False
        assert task.direction == MovementDirection.UP
        assert task.distance == 2

    def test_run(self, task):
        pass


class TestBurningTaskSuite:
    @pytest.fixture
    def task(self, game, fire):
        game.add(fire)
        return BurningTask(game, fire)

    def test_init(self, task, game, fire):
        assert task.game == game
        assert task.task_manager == game.tasks
        assert task.board == game.board
        assert task.entity == fire
        assert task.last_update is None
        assert task.started is False
        assert task.done is False

    def test_run(self, task):
        pass


class TestDetonationTaskSuite:
    @pytest.fixture
    def task(self, game, bomb, player):
        game.add(bomb)
        game.add(player)
        return DetonationTask(game, bomb, player)

    def test_init(self, task, game, bomb, player):
        assert task.game == game
        assert task.task_manager == game.tasks
        assert task.board == game.board
        assert task.entity == bomb
        assert task.last_update is None
        assert task.started is False
        assert task.done is False
        assert task.bomb_owner == player

    def test_run(self, task):
        duration = task.entity.duration
        task.run()
        assert task.started is True
        assert task.done is False
        time.sleep(duration/2)
        task.run()
        assert task.started is True
        assert task.done is False
        assert 0 < task.entity.duration < duration
        time.sleep(duration/2)
        task.run()
        assert task.done is True
        assert task.entity.duration <= 0
        assert task.entity.detonating is False
        assert task.entity.destroyed is True
        for space in task.board.blast_radius(task.entity.logical_location, task.entity.radius):
            assert space.has_fire()


