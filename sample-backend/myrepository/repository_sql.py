from .abstract_repository import AbstractRepository
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json

DB_NAME = "postgres"
TABLE_NAME = "sample_table"
HOST_NAME = "localhost"
PAGE_LIMIT = 10


class RepositoryPostgres(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в базе данных MySQL.
    Используется доступ по логину и паролю
    Класс может быть создан при помощи фабрики RepositoryFactory в качестве одного из дух возможных вариантов.
    Другая возможность - использовать репозиторий RepositoryList.
    """

    def __init__(self, options: dict):
        """
        Простая инициализация
        :param options: словарь параметров. Для данного репозитория используются параметры username, password
        """
        self.__options = options  # Сохранить настройки
        self.__init_db()  # Инициализировать базу данных
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

    def __make_query(self, query: str, entity=AbstractRepository.template) -> list:
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
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
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
        results = self.__make_query(f"DROP TABLE public.{TABLE_NAME};")  # удаляем таблицу из предыдущих запусков
        print(results)
        # далее создать таблицу.
        #   id: целочисленное без автоматического инкремента
        #   title: строковое с максимальной длинной 255
        results = self.__make_query(f"""
CREATE TABLE IF NOT EXISTS public.sample_table
(
    id integer NOT NULL,
    title character varying(255),
    value character varying(255),
    PRIMARY KEY (id)
);

ALTER TABLE public.sample_table
    OWNER to postgres;""")
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
        current_entity = entity.copy()
        current_entity.pop('id')
        keys_list = list(current_entity.keys())
        if len(keys_list) == 1:
            keys = keys_list[0]
        else:
            keys = f'({", ".join(list(entity.keys())[1:])})'
        # print(keys)
        return keys

    @staticmethod
    def __format_values_no_id(entity: dict) -> str:
        current_entity = entity.copy()
        current_entity.pop('id')
        values_list = list(current_entity.keys())
        if len(values_list) == 1:
            values = f"%({values_list[0]})s"
        else:
            values = "(%(" + ")s, %(".join(values_list) + ")s)"
        # print(values)
        return values

    def get(self, entity_id: int) -> dict:
        """
        Возвращает одного пользователя по id.
        Использует простой кэш на словаре.
        :param entity_id: целочисленное значение id пользователя
        :return: если пользователь найден в базе, то возвращает сущность пользователя, иначе возвращает {}
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

    def index(self) -> list[dict]:
        """
        Возвращает все сущности из репозитория
        :return: если репозиторий не пуст, то возвращает список c сущностями из него, иначе возвращает []
        """
        entities_list = self.__make_query(f"SELECT * FROM {TABLE_NAME}")
        if entities_list is None:
            return []
        return entities_list

    def list_paginated(self, page: int) -> list[dict]:
        """
        Возвращает пользователей в базе постранично
        :param page: номер страницы, начиная с 1
        :return: если репозиторий не пуст, то возвращает список c сущностями из него, иначе возвращает []
        """
        offset = (page - 1) * PAGE_LIMIT
        entities_list = self.__make_query(f"SELECT * FROM {TABLE_NAME} LIMIT {PAGE_LIMIT} OFFSET {offset}")
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
                                SET {keys} = {values} 
                                WHERE id = %(id)s RETURNING id;""",
                              entity=entity)
            self.__clear_cache()
            return 0
        return -1
