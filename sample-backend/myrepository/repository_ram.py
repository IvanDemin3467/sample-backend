from .abstract_repository import AbstractRepository
from .helpers import measure_time

PAGE_LIMIT = 10


class RepositoryBytearray(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в массиве байтов.
    Работает быстрее, чем RepositoryList, так как сложность чтения О(1)
    Но есть ограничения:
        фиксированная длина записи
        сложнее удалять записи из репозитория
    Он может быть создан при помощи RepositoryFactory в качестве одного из возможных вариантов.
    """
    __id_length = 2
    __title_length = 40
    __entry_length = __title_length
    __db_length = 15

    def __init__(self, options: dict):
        """
        Простая инициализация
        Формат репозитория: bytearray
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__db = bytearray(self.__title_length * self.__db_length)  # Инициализируется база пользователей.

    def __get_address(self, user_id: int) -> tuple[int, int]:
        """
        Вспомогательная функция.Преобразует ID сущности в начальный и конечный адрес в репозитории
        :param user_id: entity_id: целочисленное значение id сущности
        :return: кортеж, состоящий из первого и конечного адресов в репозитории
        """
        first_byte = (user_id - 1) * self.__entry_length
        last_byte = first_byte + self.__entry_length
        return first_byte, last_byte

    @measure_time
    def get(self, entity_id: int) -> dict:
        """
        Возвращает из репозитория одну сущность по переданному id
        :param entity_id: целочисленное значение id сущности
        :return: если сущность найдена в репозитории, то возвращает сущность, иначе возвращает {}
        """
        first_byte, last_byte = self.__get_address(entity_id)
        if self.__db[first_byte] != 0:
            response = self.__db[first_byte:last_byte].rstrip(b"\x00").decode("utf-8")
            return self.get_template(entity_id, response)
        return {}

    @measure_time
    def index(self) -> list[dict]:
        """
        Возвращает все сущности из репозитория
        :return: если репозиторий не пустой, то возвращает список c сущностями из него, иначе возвращает []
        """
        results = []
        for i in range(self.__db_length):
            first_byte, last_byte = self.__get_address(i)
            if self.__db[first_byte] != 0:
                response = self.__db[first_byte:last_byte].rstrip(b"\x00").decode("utf-8")
                results.append(self.get_template(i, response))
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
        results = []
        offset = (page - 1) * PAGE_LIMIT
        limit = offset + PAGE_LIMIT
        for i in range(limit, offset):
            first_byte, last_byte = self.__get_address(i)
            if self.__db[first_byte] != 0:
                response = self.__db[first_byte:last_byte].rstrip(b"\x00").decode("utf-8")
                results.append(self.get_template(i, response))
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
        first_byte, last_byte = self.__get_address(entity["id"])
        to_db = bytearray(str(entity), 'utf-8')
        if self.__db[first_byte] == 0:
            for i in range(len(to_db)):
                self.__db[first_byte + i] = to_db[i]
            return 0
        return -1

    @measure_time
    def delete(self, entity_id: int) -> int:
        """
        Удаляет одну сущность из репозитория
        :param entity_id: целочисленное значение id сущности
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        first_byte, last_byte = self.__get_address(entity_id)
        if self.__db[first_byte] != 0:
            for i in range(self.__entry_length):
                self.__db[first_byte + i] = 0
            return 0
        return -1

    @measure_time
    def update(self, entity: dict) -> int:
        """
        Обновляет данные сущности в репозитории в соответствии с переданными параметрами
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает 0, иначе возвращает -1
        """
        first_byte, last_byte = self.__get_address(entity["id"])
        title = entity["title"]
        to_db = bytearray(title, 'utf-8')
        if self.__db[first_byte] != 0:
            for i in range(len(to_db)):
                self.__db[first_byte + i] = to_db[i]
            return 0
        return -1


class RepositoryList(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в оперативной памяти.
    Он может быть создан при помощи RepositoryFactory в качестве одного из дух возможных вариантов.
    Другая возможность - использовать репозиторий RepositoryMySQL
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
