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
            entity.destroy()
        elif isinstance(entity, entities.Modifiable) and space.modifier:
            space.modifier.modify(entity)
            space.modifier.destroy()

    def all_entities(self):
        return self._entities.all_entities()

    def drop_bomb(self, entity):
        if isinstance(entity, entities.Player) and not entity.is_moving and entity.bombs:
            bomb = entities.Bomb(owner=entity, location=entity.logical_location)
            entity.bombs -= 1
            self.add(bomb)
            bomb.detonate_set()

    def move(self, entity, direction, num_spaces):
        new_location = self._board.get_relative_location(entity.logical_location, direction)
        space = self._board.get(new_location)
        if isinstance(entity, entities.Movable):
            if not space.has_collision():
                self._board.remove(entity)
                entity.move_set(new_location, direction, num_spaces)
                self._board.add(entity)
            else:
                entity.move_reset()

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
                            space.modifier.destroy()
                        # we now process whether the entity has walked into a fire and needs to be killed.
                        if space.has_active_fire() and isinstance(entity, entities.Destroyable):
                            entity.destroy()
                        if entity.movement_spaces:
                            self.move(entity, entity.movement_direction, entity.movement_spaces)

                # handle fire processing
                if isinstance(entity, entities.Burnable) and entity.is_burning:
                    entity.burn_update()
                    # if the entity is no longer burning, it's finished.
                    if not entity.is_burning:
                        entity.destroy()

                # handle detonation processing
                if isinstance(entity, entities.Detonatable) and entity.is_detonating:
                    entity.detonate_update()
                    # if the entity is no longer detonating, it's finished.
                    if not entity.is_detonating:
                        # determine the blast radius and destroy all destructible entities within.
                        for location in self._board.blast_radius(entity.logical_location, entity.fire_distance):
                            space = self._board.get(location)
                            for to_destroy in space.destructible_entities():
                                to_destroy.destroy()
                            fire = entities.Fire(location=location)
                            self.add(fire)
                            fire.burn_set()
                        # set this entity to be removed
                        entity.destroy()
                        # if the bomb belonged to someone, give them a bomb
                        if entity.owner:
                            entity.owner.bombs += 1

            # regardless of whether anything has been done, update this entity's update time.
            entity.last_update = time.time()

            # finally, if this entity has been destroyed, remove it from the game.
            if entity.is_destroyed:
                self.remove(entity)

    def remove(self, entity):
        self._entities.remove(entity)
        self._board.remove(entity)


class Board:
    def __init__(self, width, height):
        self._board = [[BoardSpace() for _ in range(0, height)] for _ in range(0, width)]
        self.width = width
        self.height = height

    def add(self, entity):
        self._board[entity.logical_location.x][entity.logical_location.y].add(entity)

    def all_entities(self):
        return [entity for row in self._board for space in row for entity in space.all_entities()]

    def blast_radius(self, location, radius):
        to_return = [location]

        for direction in entities.MovementDirection.all_directions():
            for distance in range(1, radius):
                potential_location = self.get_relative_location(location, direction, distance)
                space = self.get(potential_location)
                if space.has_indestructible_entities():
                    break
                to_return.append(potential_location)
        return to_return

    def dimensions(self):
        return utils.Coordinate(self.width, self.height)

    def get(self, location):
        return self._board[location.x][location.y]

    def get_relative_location(self, location, direction, distance=1):
        new_location = [
            *location
        ]
        if direction == entities.MovementDirection.UP:
            new_location[1] -= distance
        elif direction == entities.MovementDirection.DOWN:
            new_location[1] += distance
        elif direction == entities.MovementDirection.LEFT:
            new_location[0] -= distance
        elif direction == entities.MovementDirection.RIGHT:
            new_location[0] += distance
        for index, (loc, dim) in enumerate(zip(new_location, self.dimensions())):
            if loc < 0:
                new_location[index] += dim
            if loc >= dim:
                new_location[index] -= dim
        return utils.Coordinate(*new_location)

    def remove(self, entity):
        self._board[entity.logical_location.x][entity.logical_location.y].remove(entity)


class EntityMap:
    def __init__(self):
        self._entities = {}

    def add(self, entity):
        self._entities[entity.unique_id] = entity

    def all_entities(self):
        return self._entities.values()

    def get(self, unique_id):
        return self._entities[unique_id] if unique_id in self._entities else None

    def remove(self, entity):
        self._entities.pop(entity.unique_id) if entity.unique_id in self._entities else None


class BoardSpace:
    def __init__(self):
        self.modifier = None
        self.fire = None
        self.bomb = None
        self.entity = None

    def add(self, entity):
        setattr(self, self._entity_to_attribute(entity), entity)

    def all_entities(self):
        return [entity for entity in [self.modifier, self.fire, self.bomb, self.entity] if entity is not None]

    def destructible_entities(self):
        return [entity for entity in self.all_entities() if isinstance(entity, entities.Destroyable)]

    def has_active_fire(self):
        return self.fire is not None and self.fire.is_burning and not self.fire.is_destroyed

    def has_active_modifier(self):
        return self.modifier is not None and not self.modifier.is_destroyed

    def has_collision(self):
        return self.bomb is not None or isinstance(self.entity, entities.Collideable)

    def has_indestructible_entities(self):
        for entity in self.all_entities():
            if not isinstance(entity, entities.Destroyable):
                return True
        return False

    def remove(self, entity):
        setattr(self, self._entity_to_attribute(entity), None)

    @staticmethod
    def _entity_to_attribute(entity):
        if isinstance(entity, entities.Bomb):
            return "bomb"
        elif isinstance(entity, entities.Modifier):
            return "modifier"
        elif isinstance(entity, entities.Fire):
            return "fire"
        return "entity"
