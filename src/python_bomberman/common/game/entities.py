import uuid
from python_bomberman.common.game.exceptions import GameException


class Entity(object):
    def __init__(
            self,
            location,
            unique_id=uuid.uuid4(),
            can_move=False,             # is this entity capable of moving
            can_destroy=False,          # is this entity capable of being destroyed by other entities
            can_collide=False,          # is this entity capable of being collided with
            can_burn=False,             # is this entity capable of burning
            can_modify=False,           # is this entity capable of modifying other entities
            can_drop_bombs=False,       # is this entity capable of dropping bombs
            can_be_modified=False,      # is this entity capable of being modified by modifiers
            can_detonate=False          # is this entity capable of blowing up
    ):
        self.unique_id = unique_id
        self.physical_location = location
        self.logical_location = location

        # some attributes for communicating state
        self.destroyed = False
        self.moving = False
        self.detonating = False
        self.burning = False

        # some attributes for communicating what entities can or can't do.
        self.can_move = can_move
        self.can_drop_bombs = can_drop_bombs
        self.can_destroy = can_destroy
        self.can_collide = can_collide
        self.can_burn = can_burn
        self.can_modify = can_modify
        self.can_be_modified = can_be_modified
        self.can_detonate = can_detonate


class IndestructibleWall(Entity):
    identifier = "indestructible_wall"

    def __init__(self, location):
        super().__init__(location, can_collide=True)


class DestructibleWall(Entity):
    identifier = "destructible_wall"

    def __init__(self, location):
        super().__init__(location, can_collide=True, can_destroy=True)


class Player(Entity):
    identifier = "player"

    def __init__(self, location):
        super().__init__(
            location, can_move=True, can_collide=True, can_destroy=True, can_be_modified=True, can_drop_bombs=True
        )
        self.movement_speed = 1
        self.bombs = 1
        self.bomb_radius = 3


class Bomb(Entity):
    identifier = "bomb"

    def __init__(self, location, radius, duration=2):
        super().__init__(location, can_move=True, can_detonate=True, can_collide=True)
        self.movement_speed = 1
        self.duration = duration
        self.radius = radius


class Fire(Entity):
    identifier = "fire"

    def __init__(self, location, duration=2):
        super().__init__(location, can_destroy=True, can_burn=True)
        self.duration = duration


class Modifier(Entity):
    def __init__(self, location, amount):
        super().__init__(location, can_destroy=True, can_modify=True)
        self.amount = amount

    def modify(self, entity):
        raise GameException.method_unimplemented(self.__class__, "modify")


class BombModifier(Modifier):
    identifier = "bomb_modifier"

    def __init__(self, location, amount=1):
        super().__init__(location, amount)

    def modify(self, entity):
        entity.bombs += self.amount


class BombRadiusModifier(Modifier):
    identifier = "bomb_radius_modifier"

    def __init__(self, location, amount=1):
        super().__init__(location, amount)

    def modify(self, entity):
        entity.bomb_radius += self.amount


class MovementSpeedModifier(Modifier):
    identifier = "movement_speed_modifier"

    def __init__(self, location, amount=.1):
        super().__init__(location, amount)

    def modify(self, entity):
        entity.movement_speed += self.amount
