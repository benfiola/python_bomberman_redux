import python_bomberman.common.game.entities as entities
from python_bomberman.common.game.exceptions import GameException


class BoardSpace:
    def __init__(self):
        self.modifier = None
        self.fire = None
        self.bomb = None
        self.entity = None

    def add(self, entity):
        attr = self._entity_to_attribute(entity)
        if getattr(self, attr, None) is not None:
            raise GameException.entity_at_location_exists(entity)
        setattr(self, attr, entity)

    def all_entities(self):
        return [entity for entity in [self.modifier, self.fire, self.bomb, self.entity] if entity is not None]

    def remove(self, entity):
        attr = self._entity_to_attribute(entity)
        if getattr(self, attr, None) is None:
            raise GameException.entity_at_location_doesnt_exist(entity)
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

    def occupied(self, entity):
        return getattr(self, self._entity_to_attribute(entity), None) is not None

    def has_modifier(self):
        return self.modifier is not None and not self.modifier.destroyed

    def has_fire(self):
        return self.fire is not None and not self.fire.destroyed

    def has_bomb(self):
        return self.bomb is not None and not self.bomb.destroyed

    def has_indestructible_entity(self):
        return self.entity is not None and not self.entity.can_be_destroyed

    def destroy_all(self):
        for entity in [entity for entity in self.all_entities() if entity.can_be_destroyed]:
            entity.destroyed = True
