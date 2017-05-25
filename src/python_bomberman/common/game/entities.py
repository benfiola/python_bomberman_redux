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


class Movable(Entity):
    def __init__(self, movement_speed, **kwargs):
        super().__init__(**kwargs)
        self.is_moving = False
        self.movement_speed = movement_speed

    def _new_movement_location(self, duration):
        """
        Calculates the new movement location using self.logical_location as the target
        and self.physical_location as the current location
        :param duration: Duration of time since last update in seconds
        :return: a Coordinate object representing the new location of the entity.
        """
        list_vec = []
        for index, (l_loc, p_loc) in enumerate(zip(self.logical_location, self.physical_location)):
            # We tend to move in a single direction making this pretty easy.
            # If our current location and target location are the same, we're not moving
            # in that direction, so set this component's value to 0.
            if l_loc == p_loc:
                distance = 0
            else:
                # Otherwise, we take the product of self.movement_speed and duration,
                # negating it if we're intending to move in the other direction.
                distance = (self.movement_speed * duration)
                if l_loc - p_loc < 0:
                    distance = -list_vec[index]
            # At this point we have a movement vector reflecting the number of units
            # we want to move in a given direction for each component, so we just
            # add this number to our physical location to get our next location.
            new_coordinate = p_loc + distance
            list_vec.append(new_coordinate)
        return Coordinate(*list_vec)

    def move_update(self):
        """
                Moves an entity towards its logical location.
                :return: None
                """
        done_moving = True
        curr_time = time.time()

        new_location = self._new_movement_location(curr_time - self.last_update)

        # This block will evaluate if our new_location has reached or surpassed our target.
        # For both components, if we've reached or surpassed our target, then we're done moving.
        for (l_loc, n_loc, p_loc) in zip(self.logical_location, new_location, self.physical_location):
            p_distance = l_loc - p_loc
            n_distance = l_loc - n_loc
            done_moving = done_moving and (
                p_distance <= 0 <= n_distance or
                n_distance <= 0 <= p_distance
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


class Player(Movable, Destroyable, Collideable):
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
