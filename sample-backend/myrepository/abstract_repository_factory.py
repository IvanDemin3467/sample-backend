from abc import ABC, abstractmethod
from .abstract_repository import AbstractRepository


class AbstractRepositoryFactory(ABC):
    """
    Это интерфейс к фабрике репозиториев. Предполагает реализацию только одного классового метода create()
    """

    @classmethod
    @abstractmethod
    def create(cls) -> AbstractRepository:
        raise NotImplementedError
