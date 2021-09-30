from __future__ import annotations

import json  # to read options from file
import sys  # for repository factory (it creates class by name (string))
import psycopg2
from psycopg2.extras import RealDictCursor

import time

from myfactory import *


def measure_time(func):
    def inner(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            ex_time = time.time() - start_time
            print(f'Execution time: {ex_time:.2f} seconds')

    return inner


def memoize(func):
    _cache = {}

    def wrapper(*args, **kwargs):
        name = func.__name__
        key = (name, args, frozenset(kwargs.items()))
        if key in _cache:
            return _cache[key]
        response = func(*args, **kwargs)
        _cache[key] = response
        return response

    return wrapper


OPTIONS_FILE_PATH = "options.json"
DB_NAME = "postgres"
TABLE_NAME = "sample_table"
HOST_NAME = "localhost"
ENTITY_TEMPLATE = {'id': -1,
                   'title': 'Y Combinator',
                   'url': 'http://ycombinator.com',
                   'created_at': '2006-10-09T18:21:51.000Z',
                   'points': 0,
                   'num_comments': 0}


# Repository start
class AbstractRepository(ABC):
    """
    Абстрактный репозиторий для работы с сущностями Entity
    Предполагает реализацию методов get(), list(), add(), delete(), update()
    """
    template = ENTITY_TEMPLATE
    template_keys = list(ENTITY_TEMPLATE.keys())

    @abstractmethod
    def get(self, reference) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def add(self, entity: dict) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete(self, reference) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, reference) -> int:
        raise NotImplementedError

    def get_template(self, entity_id=0, par1="filer") -> dict:
        result = self.template.copy()
        result["id"] = entity_id
        result[self.template_keys[1]] = par1
        return result


class RepositoryBytearray(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в массиве байтов.
    Работает быстрее, чем repositoryRAM, так как сложность чтения О(1)
    Но есть ограничения:
        фиксированная длина записи
        сложнее удалять записи из репозитория
    Он может быть создан при помощи RepositoryCreator в качестве одного из возможных вариантов.
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
    def list(self) -> list[Entity]:
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
    Он может быть создан при помощи RepositoryCreator в качестве одного из дух возможных вариантов.
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
    def list(self) -> list[Entity]:
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


class RepositoryPostgres(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в базе данных MySQL.
    Используется доступ по логину и паролю
    Класс может быть создан при помощи фабрики RepositoryCreator в качестве одного из дух возможных вариантов.
    Другая возможность - использовать репозиторий RepositoryRAM.
    """

    def __init__(self, options: dict):
        """
        Простая инициализация
        :param options: словарь параметров. Для данного репозитория используются параметры username, password
        """
        self.__options = options  # Сохранить настройки
        # self.__init_db()  # Инициализировать базу данных
        self._cache = {}  # Инициализировать простой кэш

    def __get_db_connection(self) -> psycopg2.connect:
        """
        Вспомогательная процедура для создания подключения к базе данных, расположенной на локальном компьютере.
        В качестве параметров использует логин и пароль, хранимые в словаре __options.
        В качестве имени базы использует значение глобальной константы DB_NAME
        :return: если подключение к базе успешно, то возвращает объект mysql.connector.connect, иначе возвращает None
        """
        try:
            return psycopg2.connect(dbname=DB_NAME,
                                    user=self.__options['username'],
                                    password=self.__options['password'],
                                    host=HOST_NAME)
            # return psycopg2.connect(f"""postgres://
            #                                 {self.__options['username']}:
            #                                 {self.__options['password']}@
            #                                 0.0.0.0/
            #                                 {DB_NAME}""")
        except BaseException as err:
            print(err)
            return None

    def __make_query(self, query: str, entity=ENTITY_TEMPLATE) -> list:
        """
        Вспомогательная процедура для создания запросов к базе данных
        Использует передачу именованных параметров для противостояния атакам SQL injection
        Если при вызове передан небезопасный запрос, то исключения не возникает
        :param query: строка запроса к базе, отформатированная в соответствии со стандартами MySQL
        :param entity: словарь с параметрами сущности; содержит целочисленное значение id
        :return: возвращает ответ от базы данных.
        Это может быть список словарей с параметрами сущностей в случае запроса SELECT,
            либо пустая строка в других случаях
        Если запрос к базе возвращает исключение, то данная процедура возвращает []
        """
        try:
            conn = self.__get_db_connection()  # Создать подключение
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, entity)  # выполнить запрос безопасным образом
                print(query, entity)
                results = cur.fetchall()  # получить результаты выполнения
                results = json.dumps(results)
                results = json.loads(results)
                print(results)
                cur.close()  # вручную закрыть курсор
            conn.commit()  # вручную указать, что транзакции завершены
            conn.close()  # вручную закрыть соединение
            return results
        except BaseException as err:
            print(f"Error with db: {err}")
            return []

    def __init_db(self) -> int:
        """
        Инициализация базы данных
        :return: возвращает всегда 0, так как исключения обрабатываются в вызываемой процедуре __make_query()
        """
        # results = self.__make_query(
        #     f"CREATE DATABASE {DB_NAME};")  # создать базу с именем DB_NAME, если не существует
        results = self.__make_query(f"DROP TABLE {TABLE_NAME};")  # удаляем таблицу из предыдущих запусков
        print(results)
        # далее создать таблицу.
        #   id: целочисленное без автоматического инкремента
        #   title: строковое с максимальной длинной 255
        results = self.__make_query(f"""CREATE TABLE {TABLE_NAME} 
                                        (id SERIAL PRIMARY KEY, 
                                        {self.template_keys[1]} VARCHAR(255) NOT NULL)
                                        """)
        print(results)
        return 0

    def __clear_cache(self) -> None:
        """
        Clears cache. Use it on every DB-changing operation
        :return: None
        """
        self._cache = {}

    @staticmethod
    def __format_keys(entity: dict) -> str:
        keys = ", ".join(list(entity.keys()))
        # print(keys)
        return keys

    @staticmethod
    def __format_values(entity: dict) -> str:
        values = "%(" + ")s, %(".join(list(entity.keys())) + ")s"
        # print(values)
        return values

    @staticmethod
    def __format_keys_no_id(entity: dict) -> str:
        keys = ", ".join(list(entity.keys())[1:])
        # print(keys)
        return keys

    @staticmethod
    def __format_values_no_id(entity: dict) -> str:
        values = "%(" + ")s, %(".join(list(entity.keys())[1:]) + ")s"
        # print(values)
        return values

    def get(self, entity_id: int) -> dict:
        """
        Возвращает одного пользователя по id.
        Использует простой кэш на словаре.
        :param entity_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает сущность пользователя, иначе возвращает пустую сущность
        """
        key = ("get", entity_id)
        if key in self._cache:
            results = self._cache[key]
        else:
            params = self.get_template(entity_id=entity_id)
            results = self.__make_query(f"SELECT * FROM {TABLE_NAME} WHERE id = %(id)s", params)
            self._cache[key] = results

        try:
            return results[0]
        except IndexError:
            return {}

    def list(self) -> list[dict]:
        """
        Возвращает всех пользователей в базе
        :return: если репозиторий не пуст, то возвращает список c сущностями из него, иначе возвращает []
        """
        entities_list = self.__make_query(f"SELECT * FROM {TABLE_NAME}")
        if entities_list is None:
            return []
        return entities_list

    def add(self, entity: dict) -> int:
        """
        Добавляет новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        keys = self.__format_keys(entity)
        values = self.__format_values(entity)
        if self.get(entity["id"]) == {}:
            self.__make_query(f"""INSERT INTO {TABLE_NAME} ({keys}) 
                              VALUES ({values}) RETURNING id;""",
                              entity=entity)
            self.__clear_cache()
            return 0
        return -1

    def delete(self, entity_id: int) -> int:
        """
        Удаляет одну сущность из репозитория по id
        :param entity_id: целочисленное значение id сущности
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        if self.get(entity_id) != {}:
            params = self.get_template(entity_id=entity_id)
            self.__make_query(f"DELETE FROM {TABLE_NAME} WHERE id = %(id)s RETURNING id;", entity=params)
            self.__clear_cache()
            return 0
        return -1

    def update(self, entity: dict) -> int:
        """
        Обновляет хранимую сущность в соответствии с переданным параметром
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает обновляет её и возвращает 0, иначе возвращает -1
        """
        if self.get(entity["id"]) != {}:
            keys = self.__format_keys_no_id(entity)
            values = self.__format_values_no_id(entity)
            self.__make_query(f"""UPDATE {TABLE_NAME} 
                                SET ({keys}) = ({values}) 
                                WHERE id = %(id)s RETURNING id;""",
                              entity=entity)
            self.__clear_cache()
            return 0
        return -1


class AbstractRepositoryCreator(ABC):
    """
    Это интерфейс к фабрике репозиториев. Предполагает реализацию только одного классового метода create()
    """
    template = ENTITY_TEMPLATE

    @classmethod
    @abstractmethod
    def create(cls) -> AbstractRepository:
        raise NotImplementedError


class RepositoryCreator(AbstractRepositoryCreator):
    """
    Это класс-фабрика репозиториев. Он возвращает в качестве репозитория один из двух инстансов:
        RepositoryMySQL для хранения записей пользователей в MySQL базе данных или
        RepositoryRAM для хранения записей пользователей в оперативной памяти.
    Также класс умеет загружать настройки программы из файла при помощи метода __get_options()
    Единственный доступный извне метод - классовый метод create(), возвращающий выбранный репозиторий
    """

    @staticmethod
    def __get_options():
        """
        Вспомогательный статический метод.
        Считывает настройки программы из файла OPTIONS_FILE_PATH.
        :return: словарь с настройками
            repo_type: содержит имя класса, который будет создаваться этой фабрикой репозиториев. Возможные значения:
                RepositoryMySQL - хранит сущности в базе MySQL
                RepositoryRAM - хранит сущности в оперативной памяти
            username: логин для доступа к базе
            password: пароль для доступа к базе
        """

        options = {"use_db_repo": False, "username": None, "password": None}  # настройки по умолчанию

        try:
            json_file = open(OPTIONS_FILE_PATH)
            json_object = json.load(json_file)
            json_file.close()
        except OSError:
            print("Got exception while reading options from file")
            return options

        try:
            options["repo_type"] = json_object['repo_type']
            options["username"] = json_object['username']
            options["password"] = json_object['password']
        except KeyError:
            print(f"The file {OPTIONS_FILE_PATH} is not formatted correctly")

        return options

    @classmethod
    def create(cls) -> AbstractRepository:
        """
        Выбирает тип используемого репозитория в зависимости от параметра repo_type, полученного из файла
        :return: инстанс выбранного репозитория
        """
        options = cls.__get_options()
        repository_class = getattr(sys.modules[__name__], options["repo_type"])
        repository = repository_class(options)
        print("Working with", repository)
        return repository
