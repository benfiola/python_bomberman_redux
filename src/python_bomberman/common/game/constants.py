class MovementDirection(object):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

    @staticmethod
    def all_directions():
        return [MovementDirection.UP, MovementDirection.DOWN, MovementDirection.LEFT, MovementDirection.RIGHT]