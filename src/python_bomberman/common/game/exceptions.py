class GameException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    @classmethod
    def space_occupied(cls, location, attr, entity):
        return cls("Board space at location {} already has an entity for {} - cannot add entity {}".format(location, attr, entity))

    @classmethod
    def space_not_occupied(cls, location, attr, entity):
        return cls("Board space at location {} has no entity for {} - unable to remove {}.".format(location, attr, entity))