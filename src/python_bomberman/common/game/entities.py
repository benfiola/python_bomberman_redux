import time
from uuid import uuid4
from python_bomberman.common.utils import Coordinate


class Entity(object):
    def __init__(self, location, **kwargs):
        unique_id = kwargs.pop("unique_id", None)
        if unique_id is None:
            unique_id = uuid4()

        self.logical_location = location
        self.physical_location = location
        self.unique_id = unique_id
        self.last_update = time.time()

        self.is_destroyed = False


class Modifiable(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Collideable(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MovementDirection(object):
    LEFT = 0
    DOWN = 1
    UP = 2
    RIGHT = 3


class Movable(Entity):
    def __init__(self, movement_speed, **kwargs):
        super().__init__(**kwargs)
        self.is_moving = False
        self.movement_direction = None
        self.movement_speed = movement_speed

    def _new_movement_location(self, duration, board_dimensions):
        """
        Calculates the new movement location using self.logical_location as the target
        and self.physical_location as the current location
        :param duration: Duration of time since last update in seconds
        :return: a Coordinate object representing the new location of the entity.
        """
        coords = [
            *self.physical_location
        ]
        distances = [0, 0]

        if self.movement_direction in [MovementDirection.LEFT, MovementDirection.RIGHT]:
            distances[0] = self.movement_speed * duration
            if self.movement_direction == MovementDirection.LEFT:
                distances[0] = -distances[0]
        if self.movement_direction in [MovementDirection.UP, MovementDirection.DOWN]:
            distances[1] = self.movement_speed * duration
            if self.movement_direction == MovementDirection.UP:
                distances[1] = -distances[1]

        for index, (coord, dist, dimension) in enumerate(zip(coords, distances, board_dimensions)):
            coords[index] = coord + dist

            # if we're heading off the board, let's use this opportunity
            # to teleport ourselves onto the other side of the board, moving
            # to our target location.
            if coords[index] < -0.5:
                coords[index] += dimension
            elif coords[index] > (dimension - .5):
                coords[index] -= dimension

        return Coordinate(*coords)

    def move_update(self, board_dimensions):
        """
        Moves an entity towards its logical location.
        :return: None
        """
        done_moving = True
        curr_time = time.time()

        new_location = self._new_movement_location(curr_time - self.last_update, board_dimensions)

        # Evaluate if we're done moving by looking at movement direction and our new physical location
        done_moving = (
            (self.movement_direction == MovementDirection.LEFT and new_location[0] <= self.logical_location[0] <= self.physical_location[0]) or
            (self.movement_direction == MovementDirection.RIGHT and self.physical_location[0] <= self.logical_location[0] <= new_location[0]) or
            (self.movement_direction == MovementDirection.UP and new_location[1] <= self.logical_location[1] <= self.physical_location[1]) or
            (self.movement_direction == MovementDirection.DOWN and self.physical_location[1] <= self.logical_location[1] <= new_location[1])
        )

        # Naively update our physical location.
        self.physical_location = new_location

        # If we're done moving, ensure our physical location matches our
        # logical location, reset movement state flags, and apply modifiers
        # that might be at the spot we've just arrived at.
        if done_moving:
            self.is_moving = False
            self.physical_location = self.logical_location


class Detonatable(Entity):
    def __init__(self, bomb_duration, fire_distance, owner=None, **kwargs):
        super().__init__(**kwargs)
        self.is_detonating = False
        self.fire_distance = fire_distance
        self.owner = owner
        self.bomb_duration = bomb_duration

    def detonate_update(self):
        curr_time = time.time()
        duration = curr_time - self.last_update
        self.bomb_duration -= duration
        if self.bomb_duration <= 0:
            self.is_detonating = False


class Burnable(Entity):
    def __init__(self, fire_duration, **kwargs):
        super().__init__(**kwargs)
        self.is_burning = False
        self.fire_duration = fire_duration

    def burn_update(self):
        curr_time = time.time()
        duration = curr_time - self.last_update
        self.fire_duration -= duration
        if self.fire_duration <= 0:
            self.is_burning = False


class Destroyable(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Player(Movable, Destroyable, Collideable, Modifiable):
    identifier = "player"

    def __init__(self, location, unique_id=None):
        super().__init__(
            location=location,
            unique_id=unique_id,
            movement_speed=1
        )

        self.bombs = 1
        self.fire_distance = 3
        self.bomb_duration = 3


class Fire(Burnable, Destroyable):
    identifier = "fire"

    def __init__(self, location, unique_id=None):
        super().__init__(
            location=location,
            unique_id=unique_id,
            fire_duration=2
        )


class Bomb(Detonatable, Destroyable, Collideable):
    identifier = "bomb"

    def __init__(self, owner, location, unique_id=None):
        super().__init__(
            location=location,
            unique_id=unique_id,
            owner=owner,
            fire_distance=owner.fire_distance,
            bomb_duration=owner.bomb_duration,
        )


class DestructibleWall(Collideable, Destroyable):
    identifier = "destructible_wall"

    def __init__(self, location, unique_id=None):
        super().__init__(
            location=location,
            unique_id=unique_id
        )


class IndestructibleWall(Collideable):
    identifier = "indestructible_wall"

    def __init__(self, location, unique_id=None):
        super().__init__(
            location=location,
            unique_id=unique_id
        )


class Modifier(Destroyable):
    def __init__(self, amount, **kwargs):
        self.amount = amount
        super().__init__(
            **kwargs
        )

    def modify(self, entity):
        pass


class MovementModifier(Modifier):
    def __init__(self, location, unique_id=None):
        super().__init__(
            location=location,
            unique_id=unique_id,
            amount=.1
        )

    def modify(self, entity):
        entity.movement_speed += self.amount


class BombModifier(Modifier):
    def __init__(self, location, unique_id=None):
        super().__init__(
            location=location,
            unique_id=unique_id,
            amount=1
        )

    def modify(self, entity):
        entity.bombs += self.amount


class FireModifier(Modifier):
    def __init__(self, location, unique_id=None):
        super().__init__(
            location=location,
            unique_id=unique_id,
            amount=1
        )

    def modify(self, entity):
        entity.fire_distance += self.amount
