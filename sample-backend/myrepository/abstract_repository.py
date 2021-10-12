from abc import ABC, abstractmethod

ENTITY_TEMPLATE = {'id': -1,
                   'title': 'title',
                   'value': 'value'}


class AbstractRepository(ABC):
    """
    Абстрактный репозиторий для работы с сущностями Entity
    Предполагает реализацию методов get(), list(), add(), delete(), update()
    """
    template = ENTITY_TEMPLATE
    template_keys = list(ENTITY_TEMPLATE.keys())

    @abstractmethod
    def get(self, reference: int) -> dict:
        raise NotImplementedError

    @abstractmethod
    def index(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def list_paginated(self, page: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def add(self, entity: dict) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete(self, reference: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, reference) -> int:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str) -> list[dict]:
        raise NotImplementedError

    def get_template(self, entity_id=0, par1="filer") -> dict:
        result = self.template.copy()
        result["id"] = entity_id
        result[self.template_keys[1]] = par1
        return result
