from .abstract_repository import AbstractRepository
from .helpers import measure_time
import json

PAGE_LIMIT = 10


class RepositoryBytearray(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в массиве байтов.
    Работает быстрее, чем RepositoryList, так как сложность чтения (и других операций) О(1).
    Но есть ограничения:
        фиксированная длина записи,
        сложнее удалять записи из репозитория.
    Он может быть создан при помощи RepositoryFactory в качестве одного из возможных репозиториев.
    """
    __id_length = 2  # length of "id" field in bytes
    __field_length = 40  # length of other fields in bytes
    __db_length = 15  # amount of entities in repository

    def __init__(self, options: dict):
        """
        Простая инициализация
        Формат репозитория: bytearray
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        """
        self.__options = options  # Parameters passed to the constructor are saved
        amount_of_fields = len(self.get_template()) - 1  # Amount of fields in the template excluding the "id" field
        self.__entry_length = amount_of_fields * self.__field_length  # Length of one entry in bytes
        self.__db = bytearray(self.__entry_length * self.__db_length)  # Entity repository is initialized

    def __get_address(self, entity_id: int) -> tuple[int, int]:
        """
        Вспомогательная функция.Преобразует ID сущности в начальный и конечный адрес в репозитории
        :param entity_id: entity_id: целочисленное значение id сущности
        :return: кортеж, состоящий из первого и конечного адресов в репозитории
        """
        first_byte = (entity_id - 1) * self.__entry_length
        last_byte = first_byte + self.__entry_length
        return first_byte, last_byte

    def __read_entity(self, entity_id: int) -> dict:
        """
        Считывает из репозитория одну сущность по переданному id
        :param entity_id: целочисленное значение id сущности
        :return: если сущность найдена в репозитории, то возвращает сущность, иначе возвращает {}
        """
        if entity_id > self.__db_length:  # Check if we have overstepped
            return {}
        first_byte, last_byte = self.__get_address(entity_id)  # Get boundaries of entry in repository
        if self.__db[first_byte] == 0:  # Check if the entry is empty
            return {}
        sequence = self.__db[first_byte:last_byte]  # Read bytes from repository
        truncated = sequence.rstrip(b"\x00")  # Remove trailing zeros
        serialized = truncated.decode("utf-8")  # Convert to string
        result = json.loads(serialized)  # Convert to dict
        result["id"] = entity_id
        return result

    def __write_entry(self, entity: dict, write_if_exists=False) -> int:
        """
        Записывает новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        truncated = entity.copy()  # Prepare the object for storage.
        truncated.pop("id")  # Remove the excessive "id" field.
        serialized = json.dumps(truncated)  # Convert to string
        to_db = bytearray(serialized, 'utf-8')  # Convert to bytearray

        first_byte, _ = self.__get_address(entity["id"])  # Specify the starting byte of the record in the repository
        if self.__db[first_byte] == write_if_exists:  # Check if entry is empty (first byte is zero)
            for i in range(len(to_db)):  # Writing byte by byte
                self.__db[first_byte + i] = to_db[i]
            return 0
        return -1

    @measure_time
    def get(self, entity_id: int) -> dict:
        """
        Возвращает из репозитория одну сущность по переданному id
        :param entity_id: целочисленное значение id сущности
        :return: если сущность найдена в репозитории, то возвращает сущность, иначе возвращает {}
        """
        response = self.__read_entity(entity_id)
        return response

    @measure_time
    def index(self) -> list[dict]:
        """
        Возвращает все сущности из репозитория
        :return: если репозиторий не пустой, то возвращает список c сущностями из него, иначе возвращает []
        """
        results = []
        for entity_id in range(1, self.__db_length):
            response = self.__read_entity(entity_id)
            if response != {}:
                results.append(response)
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
        for entity_id in range(offset, limit):
            response = self.__read_entity(entity_id)
            if response != {}:
                results.append(response)
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
        return self.__write_entry(entity, write_if_exists=False)

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
        return self.__write_entry(entity, write_if_exists=True)
