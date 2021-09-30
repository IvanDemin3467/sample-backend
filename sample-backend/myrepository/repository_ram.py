from .abstract_repository import AbstractRepository
from .helpers import measure_time
from .myfactory import AbstractFactory, Entity


class RepositoryBytearray(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в массиве байтов.
    Работает быстрее, чем repositoryRAM, так как сложность чтения О(1)
    Но есть ограничения:
        фиксированная длина записи
        сложнее удалять записи из репозитория
    Он может быть создан при помощи RepositoryFactory в качестве одного из возможных вариантов.
    """
    __id_length = 2
    __title_length = 40
    __entry_length = __title_length
    __db_length = 4

    def __init__(self, options: dict, fact: AbstractFactory):
        """
        Простая инициализация
        Формат репозитория: bytearray
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        :param fact: фабрика. Используется при необходимости создать сущность Entity, возвращаемую из репозитория
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__factory = fact  # Сохраняется фабрика сущностей
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
    def get(self, user_id: int) -> Entity:
        """
        Возвращает из репозитория одну сущность по переданному id
        :param user_id: целочисленное значение id сущности
        :return: если сущность найдена в репозитории, то возвращает сущность,
            иначе возвращает пустую сущность
        """
        first_byte, last_byte = self.__get_address(user_id)
        if self.__db[first_byte] != 0:
            response = self.__db[first_byte:last_byte].rstrip(b"\x00").decode("utf-8")
            return self.__factory.create(user_id, {"title": response})
        return self.__factory.empty_entity

    @measure_time
    def index(self) -> list[Entity]:
        """
        Возвращает все сущности из репозитория
        :return: если репозиторий не пустой, то возвращает список c сущностями из него, иначе возвращает []
        """
        results = []
        for i in range(self.__db_length):
            first_byte, last_byte = self.__get_address(i)
            if self.__db[first_byte] != 0:
                response = self.__db[first_byte:last_byte].rstrip(b"\x00").decode("utf-8")
                results.append(self.__factory.create(i, {"title": response}))

        if len(results) != 0:
            return results
        return []

    @measure_time
    def add(self, entity: Entity) -> int:
        """
        Добавляет новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        first_byte, last_byte = self.__get_address(entity.id)
        title = entity.properties["title"]
        to_db = bytearray(title, 'utf-8')
        if self.__db[first_byte] == 0:
            for i in range(len(to_db)):
                self.__db[first_byte + i] = to_db[i]
            return 0
        return -1

    @measure_time
    def delete(self, user_id: int) -> int:
        """
        Удаляет одну сущность из репозитория
        :param user_id: целочисленное значение id пользователя
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        first_byte, last_byte = self.__get_address(user_id)
        if self.__db[first_byte] != 0:
            for i in range(self.__entry_length):
                self.__db[first_byte + i] = 0
            return 0
        return -1

    @measure_time
    def update(self, entity: Entity) -> int:
        """
        Обновляет данные сущности в репозитории в соответствии с переданными параметрами
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает 0, иначе возвращает -1
        """
        first_byte, last_byte = self.__get_address(entity.id)
        title = entity.properties["title"]
        to_db = bytearray(title, 'utf-8')
        if self.__db[first_byte] != 0:
            for i in range(len(to_db)):
                self.__db[first_byte + i] = to_db[i]
            return 0
        return -1


class RepositoryRAM(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в оперативной памяти.
    Он может быть создан при помощи RepositoryFactory в качестве одного из дух возможных вариантов.
    Другая возможность - использовать репозиторий RepositoryMySQL
    """

    def __init__(self, options: dict, fact: AbstractFactory):
        """
        Простая инициализация
        Формат репозитория: список сущностей Entity
        :param options: словарь параметров. В данном контроллере не используется. Нет необходимости
        :param fact: фабрика. Используется при необходимости создать сущность Entity, возвращаемую из репозитория
        """
        self.__options = options  # Сохраняются параметры, переданные в конструктор
        self.__factory = fact  # Сохраняется фабрика сущностей
        self.__db = []  # Инициализируется база пользователей.

    def __get_index(self, user_id: int) -> int:
        """
        Вспомогательная процедура для поиска индекса записи в репозитории по известному id.
        Нужна, так как репозиторий реализован в виде списка
        :param user_id: целочисленное значение id сущности
        :return: если сущность с таким id существует, то возвращает индекс, иначе возвращает -1
        """
        for i in range(len(self.__db)):
            if self.__db[i].id == user_id:
                return i
        return -1

    @measure_time
    def get(self, user_id: int) -> Entity:
        """
        Возвращает из репозитория одну сущность по переданному id
        :param user_id: целочисленное значение id сущности
        :return: если сущность найдена в репозитории, то возвращает сущность,
            иначе возвращает пустую сущность
        """
        for entity in self.__db:
            if entity.id == user_id:
                return entity
        return self.__factory.empty_entity

    @measure_time
    def index(self) -> list[Entity]:
        """
        Возвращает все сущности из репозитория
        :return: если репозиторий не пустой, то возвращает список c сущностями из него, иначе возвращает []
        """
        results = self.__db
        if len(results) != 0:
            return results
        return []

    @measure_time
    def add(self, entity: Entity) -> int:
        """
        Добавляет новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        if self.__get_index(entity.id) == -1:
            self.__db.append(entity)
            return 0
        return -1

    @measure_time
    def delete(self, user_id: int) -> int:
        """
        Удаляет одну сущность из репозитория
        :param user_id: целочисленное значение id пользователя
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        i = self.__get_index(user_id)
        if i != -1:
            del self.__db[i]
            return 0
        return -1

    @measure_time
    def update(self, entity: Entity) -> int:
        """
        Обновляет данные сущности в репозитории в соответствии с переданными параметрами
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает 0, иначе возвращает -1
        """
        i = self.__get_index(entity.id)
        if i != -1:
            self.__db[i] = entity
            return 0
        return -1
