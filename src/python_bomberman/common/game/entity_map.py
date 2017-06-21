from python_bomberman.common.game.exceptions import GameException


class EntityMap:
    def __init__(self):
        self._entities = {}

    def add(self, entity):
        if entity.unique_id in self._entities:
            raise GameException.entity_with_id_exists(entity)
        self._entities[entity.unique_id] = entity

    def all_entities(self):
        return self._entities.values()

    def destroyed_entities(self):
        return [entity for entity in self.all_entities() if entity.destroyed]

    def get(self, unique_id):
        return self._entities[unique_id] if unique_id in self._entities else None

    def remove(self, entity):
        if entity.unique_id not in self._entities:
            raise GameException.entity_with_id_doesnt_exist(entity)
        self._entities.pop(entity.unique_id) if entity.unique_id in self._entities else None
