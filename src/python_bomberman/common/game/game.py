import python_bomberman.common.game.entities as entities
import time
import python_bomberman.common.utils as utils


class Game:
    def __init__(self, game_map):
        self._board = Board(width=game_map.width, height=game_map.height)
        self._entities = EntityMap()

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

    def add(self, entity):
        self._entities.add(entity)
        self._board.add(entity)

        space = self._board.get(entity.logical_location)

        # special logic for handling modifiers added here
        # we can either add an entity on top of a modifier, or add a modifier on top of an
        # entity - in both cases, we want to immediately give the entity the modifier
        # and get rid of the modifier.
        if isinstance(space.entity, entities.Modifiable) and isinstance(entity, entities.Modifier):
            entity.modify(space.entity)
            entity.is_destroyed = True
        elif isinstance(entity, entities.Modifiable) and space.modifier:
            space.modifier.modify(entity)
            space.modifier.is_destroyed = True

    def remove(self, entity):
        self._entities.remove(entity)
        self._board.remove(entity)

    def process(self):
        for entity in list(self.all_entities()):
            # if the entity has been destroyed in this current iteration, there's no point
            # in doing anything to it - it's going to be removed in this iteration.
            if not entity.is_destroyed:
                # handle movement processing
                if isinstance(entity, entities.Movable) and entity.is_moving:
                    entity.move_update(self._board.dimensions())
                    # if the entity is not longer moving, it's finished.
                    if not entity.is_moving:
                        space = self._board.get(entity.logical_location)
                        # we now process whether the entity has walked into a modifier and can be modified.
                        if space.has_active_modifier() and isinstance(entity, entities.Modifiable):
                            space.modifier.modify(entity)
                            space.modifier.is_destroyed = True
                        # we now process whether the entity has walked into a fire and needs to be killed.
                        if space.has_active_fire() and isinstance(entity, entities.Destroyable):
                            entity.is_destroyed = True
                        if entity.movement_spaces:
                            self.move(entity, entity.movement_direction, entity.movement_spaces)

                # handle fire processing
                if isinstance(entity, entities.Burnable) and entity.is_burning:
                    entity.burn_update()
                    # if the entity is no longer burning, it's finished.
                    if not entity.is_burning:
                        entity.is_destroyed = True

                # handle detonation processing
                if isinstance(entity, entities.Detonatable) and entity.is_detonating:
                    entity.detonate_update()
                    # if the entity is no longer detonating, it's finished.
                    if not entity.is_detonating:
                        # determine the blast radius and destroy all destructible entities within.
                        for location in self._board.blast_radius(entity.logical_location, entity.fire_distance):
                            space = self._board.get(location)
                            for to_destroy in space.destructible_entities():
                                to_destroy.is_destroyed = True
                            fire = entities.Fire(location=location)
                            self.add(fire)
                            fire.is_burning = True
                        # set this entity to be removed
                        entity.is_destroyed = True
                        # if the bomb belonged to someone, give them a bomb
                        if entity.owner:
                            entity.owner.bombs += 1

            # regardless of whether anything has been done, update this entity's update time.
            entity.last_update = time.time()

            # finally, if this entity has been destroyed, remove it from the game.
            if entity.is_destroyed:
                self.remove(entity)

    def all_entities(self):
        return self._entities.all_entities()

    def move(self, entity, direction, num_spaces):
        new_location = self._get_move_location(entity, direction)
        self._set_move_state(entity, utils.Coordinate(*new_location), direction, num_spaces)

    def _get_move_location(self, entity, direction, distance=1):
        location = [
            *entity.logical_location
        ]
        if direction == entities.MovementDirection.UP:
            location[1] -= distance
        elif direction == entities.MovementDirection.DOWN:
            location[1] += distance
        elif direction == entities.MovementDirection.LEFT:
            location[0] -= distance
        elif direction == entities.MovementDirection.RIGHT:
            location[0] += distance
        for index, (loc, dim) in enumerate(zip(location, self._board.dimensions())):
            if loc < 0:
                location[index] += dim
            if loc >= dim:
                location[index] -= dim
        return utils.Coordinate(*location)

    def _set_move_state(self, entity, location, direction, num_spaces):
        space = self._board.get(location)
        if isinstance(entity, entities.Movable):
            if not space.has_collision():
                self._board.remove(entity)
                entity.movement_direction = direction
                entity.movement_spaces = num_spaces
                entity.logical_location = location
                entity.is_moving = True
                self._board.add(entity)
            else:
                entity.movement_direction = None
                entity.movement_spaces = None

    def drop_bomb(self, entity):
        if isinstance(entity, entities.Player) and not entity.is_moving and entity.bombs:
            bomb = entities.Bomb(owner=entity, location=entity.logical_location)
            entity.bombs -= 1
            self.add(bomb)
            bomb.is_detonating = True


class Board:
    def __init__(self, width, height):
        self._board = [[BoardSpace() for _ in range(0, height)] for _ in range(0, width)]
        self.width = width
        self.height = height

    def dimensions(self):
        return utils.Coordinate(self.width, self.height)

    def add(self, entity):
        self._board[entity.logical_location.x][entity.logical_location.y].add(entity)

    def remove(self, entity):
        self._board[entity.logical_location.x][entity.logical_location.y].remove(entity)

    def get(self, location):
        return self._board[location.x][location.y]

    def blast_radius(self, location, radius):
        to_return = [location]

        # TODO: replace these with generators.
        direction_lambdas = [
            lambda loc, mod: utils.Coordinate(loc.x + mod, loc.y),
            lambda loc, mod: utils.Coordinate(loc.x - mod, loc.y),
            lambda loc, mod: utils.Coordinate(loc.x, loc.y + mod),
            lambda loc, mod: utils.Coordinate(loc.x, loc.y - mod)
        ]

        for direction in direction_lambdas:
            for modifier in range(1, radius):
                potential_location = direction(location, modifier)
                space = self.get(potential_location)
                if space.has_indestructible_entities():
                    break
                to_return.append(potential_location)
        return to_return

    def all_entities(self):
        return [entity for row in self._board for space in row for entity in space.all_entities()]


class EntityMap:
    def __init__(self):
        self._entities = {}

    def add(self, entity):
        self._entities[entity.unique_id] = entity

    def remove(self, entity):
        self._entities.pop(entity.unique_id) if entity.unique_id in self._entities else None

    def get(self, unique_id):
        return self._entities[unique_id] if unique_id in self._entities else None

    def all_entities(self):
        return self._entities.values()


class BoardSpace:
    def __init__(self):
        self.modifier = None
        self.fire = None
        self.bomb = None
        self.entity = None

    def has_collision(self):
        return self.bomb is not None or isinstance(self.entity, entities.Collideable)

    def add(self, entity):
        setattr(self, self._entity_to_attribute(entity), entity)

    def remove(self, entity):
        setattr(self, self._entity_to_attribute(entity), None)

    def has_active_modifier(self):
        return self.modifier is not None and not self.modifier.is_destroyed

    def has_active_fire(self):
        return self.fire is not None and self.fire.is_burning and not self.fire.is_destroyed

    def has_indestructible_entities(self):
        for entity in self.all_entities():
            if not isinstance(entity, entities.Destroyable):
                return True
        return False

    def destructible_entities(self):
        return [entity for entity in self.all_entities() if isinstance(entity, entities.Destroyable)]

    def all_entities(self):
        return [entity for entity in [self.modifier, self.fire, self.bomb, self.entity] if entity is not None]

    @staticmethod
    def _entity_to_attribute(entity):
        if isinstance(entity, entities.Bomb):
            return "bomb"
        elif isinstance(entity, entities.Modifier):
            return "modifier"
        elif isinstance(entity, entities.Fire):
            return "fire"
        return "entity"

