from __future__ import annotations

from mysql.connector import connect, Error
import json  # to read options from file
import sys  # for repository factory (it creates class by name (string))
from abc import ABC, abstractmethod


OPTIONS_FILE_PATH = "options.json"
DB_NAME = "sample_database"
TABLE_NAME = "sample_table"


# Repository start
class AbstractRepository(ABC):
    """
    Абстрактный репозиторий для работы с сущностями Entity
    Предполагает реализацию методов get(), list(), add(), delete(), update()
    """

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
    def update(self, reference, entity: dict) -> int:
        raise NotImplementedError


class RepositoryMySQL(AbstractRepository):
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
        self.__init_db()  # Инициализировать базу данных
        self._cache = {}  # Инициализировать простой кэш

    def __get_db_connection(self) -> connect:
        """
        Вспомогательная процедура для создания подключения к базе данных, расположенной на локальном компьютере.
        В качестве параметров использует логин и пароль, хранимые в словаре __options.
        В качестве имени базы использует значение глобальной константы DB_NAME
        :return: если подключение к базе успешно, то возвращает объект mysql.connector.connect, иначе возвращает None
        """
        try:
            return connect(
                host="localhost",
                user=self.__options["username"],
                password=self.__options["password"],
                database=DB_NAME)
        except Error as err:
            print(err)
            return None

    def __make_query(self, query: str, params: dict) -> list:
        """
        Вспомогательная процедура для создания запросов к базе данных
        Использует передачу именованных параметров для противостояния атакам SQL injection
        Если при вызове передан небезопасный запрос, то исключения не возникает
        :param query: строка запроса к базе, отформатированная в соответствии со стандартами MySQL
        :param user_id: целочисленное значение id сущности для передачи в качестве параметра в запрос
        :param title: строковое значение заголовка сущности для передачи в качестве параметра в запрос
        :return: возвращает ответ от базы данных.
        Это может быть список словарей с параметрами сущностей в случае запроса SELECT,
            либо пустая строка в других случаях
        Если запрос к базе возвращает исключение, то данная процедура возвращает []
        """
        try:
            conn = self.__get_db_connection()  # Создать подключение
            with conn.cursor(dictionary=True) as cursor:  # параметр dictionary указывает, что курсор возвращает словари
                cursor.execute(query, params)  # выполнить запрос безопасным образом
                results = cursor.fetchall()  # получить результаты выполнения
                cursor.close()  # вручную закрыть курсор
            conn.commit()  # вручную указать, что транзакции завершены
            conn.close()  # вручную закрыть соединение
            return results
        except Error as err:
            print(f"Error with db: {err}")
            return []

    def __init_db(self) -> int:
        """
        date="", title="", number="", distance=""
        Инициализация базы данных
        :return: возвращает всегда 0, так как исключения обрабатываются в вызываемой процедуре __make_query()
        """
        self.__make_query(
            f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")  # создать базу с именем DB_NAME, если не существует
        self.__make_query(f"DROP TABLE IF EXISTS {TABLE_NAME};")  # удаляем таблицу из предыдущих запусков
        # далее создать таблицу.
        #   id: целочисленное без автоматического инкремента
        #   title: строковое с максимальной длинной 255
        self.__make_query(f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           date DATE,
                           title VARCHAR(255),
                           amount INTEGER,
                           distance INTEGER);""")
        return 0

    def __clear_cache(self) -> None:
        """
        Clears cache. Use it on every DB-changing operation
        :return: None
        """
        self._cache = {}

    def get(self, user_id: int):
        """
        Возвращает одного пользователя по id.
        Использует простой кэш на словаре.
        :param user_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает сущность пользователя, иначе возвращает пустую сущность
        """
        key = ("get", user_id)
        if key in self._cache:
            results = self._cache[key]
        else:
            results = self.__make_query("SELECT * FROM users WHERE id = %(user_id)s", user_id=user_id)
            self._cache[key] = results

        if len(results) == 0:
            return self.__factory.empty_entity
        entity = results[0]
        return self.__factory.create(entity["id"], {"title": entity["title"]})

    def list(self):
        """
        Возвращает всех пользователей в базе
        :return: если репозиторий не пуст, то возвращает список c сущностями из него, иначе возвращает []
        """
        entities_list = self.__make_query(f"SELECT * FROM {TABLE_NAME}")
        if len(entities_list) == 0:
            return []
        return entities_list

    @measure_time
    def add(self, entity: Entity) -> int:
        """
        Добавляет новую сущность в репозиторий
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id не существует, то возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id).id == -1:
            self.__make_query("INSERT INTO users (id, title) VALUES (%(user_id)s, %(title)s);",
                              user_id=entity.id, title=entity.properties["title"])
            self.__clear_cache()
            return 0
        return -1

    @measure_time
    def delete(self, user_id: int) -> int:
        """
        Удаляет одну сущность из репозитория по id
        :param user_id: целочисленное значение id сущности
        :return: если сущность с таким id существует на момент удаления, то возвращает 0, иначе возвращает -1
        """
        if self.get(user_id).id != -1:
            self.__make_query("DELETE FROM users WHERE id = %(user_id)s;", user_id=user_id)
            self.__clear_cache()
            return 0
        return -1

    @measure_time
    def update(self, entity: Entity) -> int:
        """
        Обновляет хранимую сущность в соответствии с переданным параметром
        :param entity: сущность с заполненными параметрами
        :return: если сущность с таким id существует, то возвращает обновляет её и возвращает 0, иначе возвращает -1
        """
        if self.get(entity.id).id != -1:
            self.__make_query("UPDATE users SET title = %(title)s WHERE id = %(user_id)s",
                              user_id=entity.id, title=entity.properties["title"])
            self.__clear_cache()
            return 0
        return -1


class AbstractRepositoryCreator(ABC):
    """
    Это интерфейс к фабрике репозиториев. Предполагает реализацию только одного классового метода create()
    """
    @classmethod
    @abstractmethod
    def create(cls, fact: AbstractFactory) -> AbstractRepository:
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
    def create(cls, fact: AbstractFactory) -> AbstractRepository:
        """
        Выбирает тип используемого репозитория в зависимости от параметра repo_type, полученного из файла
        :param fact: фабрика сущностей; передаётся репозиторию
        :return: инстанс выбранного репозитория
        """
        options = cls.__get_options()
        repository_class = getattr(sys.modules[__name__], options["repo_type"])
        repository = repository_class(options, fact)
        print("Working with", repository)
        return repository
