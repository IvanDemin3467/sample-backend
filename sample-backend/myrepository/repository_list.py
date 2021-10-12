from .abstract_repository import AbstractRepository
from .helpers import measure_time

PAGE_LIMIT = 10


class RepositoryList(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в оперативной памяти
    Работает не очень быстро. Сложность чтения (и других операций) О(n)
    Он может быть создан при помощи RepositoryFactory в качестве одного из возможных репозиториев
    """

    def __init__(self, options: dict):
        """
        Простая инициализация
        Формат репозитория: список сущностей Entity
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__db = []  # Инициализируется база пользователей.

    def __get_index(self, user_id: int) -> int:
        """
        Вспомогательная процедура для поиска индекса записи в репозитории по известному id.
        Нужна, так как репозиторий реализован в виде списка
        :param user_id: целочисленное значение id сущности
        :return: если сущность с таким id существует, то возвращает индекс, иначе возвращает -1
        """
        for i in range(len(self.__db)):
            if self.__db[i]["id"] == user_id:
                return i
        return -1

    @measure_time
    def get(self, entity_id: int) -> dict:
        """
        Возвращает из репозитория одну сущность по переданному id
        :param entity_id: целочисленное значение id сущности
        :return: если сущность найдена в репозитории, то возвращает сущность, иначе возвращает {}
        """
        for entity in self.__db:
            if entity.id == entity_id:
                return entity
        return {}

    @measure_time
    def index(self) -> list[dict]:
        """
        Возвращает все сущности из репозитория
        :return: если репозиторий не пустой, то возвращает список c сущностями из него, иначе возвращает []
        """
        results = self.__db
        if len(results) != 0:
            return results
        return []

    @measure_time
    def list_paginated(self, page: int) -> list[dict]:
        """
        Возвращает все сущности из репозитория
        :param page: номер страницы, начиная с 1
        :return: если репозиторий не пустой, то возвращает список c сущностями из него, иначе возвращает []
        """
        offset = (page - 1) * PAGE_LIMIT
        limit = offset+PAGE_LIMIT
        results = self.__db[offset:limit]
        if len(results) != 0:
            return results
        return []

    @measure_time
    def add(self, entity: dict) -> int:
        """
        Добавляет новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        if self.__get_index(entity["id"]) == -1:
            self.__db.append(entity)
            return 0
        return -1

    @measure_time
    def delete(self, entity_id: int) -> int:
        """
        Удаляет одну сущность из репозитория
        :param entity_id: целочисленное значение id пользователя
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        i = self.__get_index(entity_id)
        if i != -1:
            del self.__db[i]
            return 0
        return -1

    @measure_time
    def update(self, entity: dict) -> int:
        """
        Обновляет данные сущности в репозитории в соответствии с переданными параметрами
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает 0, иначе возвращает -1
        """
        i = self.__get_index(entity["id"])
        if i != -1:
            self.__db[i] = entity
            return 0
        return -1

    @measure_time
    def search(self, query: str) -> list[dict]:
        result = []
        for entity in self.__db:
            if query in entity["title"]:
                result.append(entity)
        return result
