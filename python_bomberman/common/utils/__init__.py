

class Coordinate(tuple):
    def __new__(cls, x, y):
        return super().__new__(cls, (x, y))

    def x(self):
        return self[0]

    def y(self):
        return self[1]
