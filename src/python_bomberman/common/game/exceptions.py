class GameException(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    @classmethod
    def location_invalid(cls, location):
        return cls("Location {} is invalid.".format(location))

    @classmethod
    def entity_at_location_exists(cls, entity):
        return cls("Entity already exists at location {}.".format(entity.logical_location))

    @classmethod
    def entity_at_location_doesnt_exist(cls, entity):
        return cls("Entity doesn't exist at location {}.".format(entity.logical_location))

    @classmethod
    def entity_with_id_exists(cls, entity):
        return cls("Entity with unique id {} already exists.".format(entity.unique_id))

    @classmethod
    def entity_with_id_doesnt_exist(cls, entity):
        return cls("Entity with unique id {} doesn't exist.".format(entity.unique_id))

    @classmethod
    def method_unimplemented(cls, class_obj, method_name):
        return cls("Class {} needs to implement method {}.".format(class_obj.__name__, method_name))

    @classmethod
    def entity_incapable_of_performing_action(cls, entity, action):
        return cls("Entity {} at location incapable of performing action: {}".format(entity.__class__.__name__, entity.logical_location, action))

    @classmethod
    def incomplete_args(cls, class_obj, method, args):
        return cls("Call to {}.{} has incomplete args: {}".format(class_obj.__name__, method, args))

