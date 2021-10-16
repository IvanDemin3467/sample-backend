from .abstract_repository import AbstractRepository
import psycopg2  # Postgres adaptor is here
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json
from .cache_lru import CacheLRU
import asyncio
import asyncpg


DB_NAME = "postgres"
TABLE_NAME = "sample_table"
HOST_NAME = "localhost"
PAGE_LIMIT = 10
CACHE_SIZE = 5


class RepositoryAsyncpg(AbstractRepository):
    """
    Это конкретная реализация репозитория для хранения сущностей Entity в базе данных PostgreSQL.
    Используется доступ по логину и паролю
    Класс может быть создан при помощи фабрики RepositoryFactory в качестве одного из возможных вариантов
    """

    def __init__(self, options: dict):
        """
        Простая инициализация
        :param options: словарь параметров. Для данного репозитория используются параметры username, password
        """
        self.__options = options  # Save options
        self.__init_db()  # Init repository
        self.__cache = CacheLRU(maxsize=CACHE_SIZE)  # LRU cache init

    def __get_db_connection(self) -> psycopg2.connect or None:
        """
        Helper procedure for creating a connection to a database located on the local computer.
        It uses the login and password stored in the __options dictionary as parameters.
        Uses the value of the global constant DB_NAME as the name of the database
        :return: if the connection to the database is successful, it returns the mysql.connector.connect object,
            otherwise it returns None
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

    def __make_query_sync(self, query: str, entity=AbstractRepository.template) -> list:
        """
        Helper procedure for creating database queries.
        Uses named parameter passing to resist SQL injection attacks
        Doesn't check the security risks of the query itself
        :param query: database query string formatted according to PostgreSQL standards
        :param entity: a dictionary with entity parameters; contains an integer 'id' value
        :return: a response from the database.
        It can be a list of dictionaries with entity parameters in the case of a SELECT query,
            or an empty string in other cases.
        If a query to the database returns an exception, then this procedure returns []
        """
        try:
            conn = self.__get_db_connection()  # Create connection
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # To allow complex tasks such as table creation
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, entity)  # Execute the request in a safe way
                print(query, entity)
                results = cur.fetchall()  # Get execution results
                results = json.dumps(results)  # Make sure the result is a list
                results = json.loads(results)
                print(results)
                cur.close()  # Manually close the cursor
            conn.commit()  # Manually indicate that transactions are complete
            conn.close()  # Manually close connection
            return results
        except BaseException as err:
            print(f"Error with db: {err}")
            return []

    async def __make_query(self, query: str, entity=AbstractRepository.template) -> list:
        conn = await asyncpg.connect(user=self.__options['username'],
                                     password=self.__options['password'],
                                     database=DB_NAME,
                                     host=HOST_NAME)
        async with conn.cursor() as cur:
            await cur.execute(query, entity)
            print(query, entity)
            results = cur.fetchall()
            print(results)
            await cur.close()
        await conn.commit()
        await conn.close()
        return results

    async def __init_db(self) -> int:
        """
        This method initializes db
        :return: always returns 0, since exceptions are handled in the called __make_query() procedure
        """
        # results = self.__make_query(
        #     f"CREATE DATABASE {DB_NAME};")  # создать базу с именем DB_NAME, если не существует
        results = await self.__make_query(f"DROP TABLE public.{TABLE_NAME};")  # Delete the table from previous runs
        print(results)
        # Create a table
        results = await self.__make_query(f"""
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

    @staticmethod
    def __format_keys(entity: dict) -> str:
        """
        Prepare string of keys for db query
        @param entity: dict of entity fields
        @return: string of keys comma separated
        """
        keys = ", ".join(list(entity.keys()))
        return keys

    @staticmethod
    def __format_values(entity: dict) -> str:
        """
        Prepare string of values for db query
        @param entity: dict of entity fields
        @return: string of values in format %(value) comma separated
        """
        values = "%(" + ")s, %(".join(list(entity.keys())) + ")s"
        return values

    @staticmethod
    def __format_keys_no_id(entity: dict) -> str:
        """
        Same as __format_keys() but excludes 'id' field.
        @param entity: dict of entity fields.
        @return: string of keys comma separated.
        """
        current_entity = entity.copy()
        current_entity.pop('id')
        keys_list = list(current_entity.keys())
        if len(keys_list) == 1:
            keys = keys_list[0]
        else:
            keys = f'({", ".join(list(entity.keys())[1:])})'
        return keys

    @staticmethod
    def __format_values_no_id(entity: dict) -> str:
        """Same as __format_values() but excludes 'id' field.
        @param entity:  dict of entity fields.
        @return: string of values in format %(value) comma separated.
        """
        current_entity = entity.copy()
        current_entity.pop('id')
        values_list = list(current_entity.keys())
        if len(values_list) == 1:
            values = f"%({values_list[0]})s"
        else:
            values = "(%(" + ")s, %(".join(values_list) + ")s)"
        # print(values)
        return values

    async def get(self, entity_id: int) -> dict:
        """
        This method returns one entity by id from the repository.
        Uses a cache on an ordered dictionary.
        :param entity_id: integer value of the entity 'id'.
        :return: if the entity is found in the repository, then it returns the entity, otherwise it returns {}.
        """
        results = self.__cache.get(entity_id)  # Try to retrieve entity from cache
        if results == -1:  # If cache miss -> perform normal db query
            print(f"Cache miss {entity_id}")
            params = self.get_template(entity_id=entity_id)  # Prepare params for query
            results = await self.__make_query(f"SELECT * FROM {TABLE_NAME} WHERE id = %(id)s", params)  # Make query
            try:
                results = results[0]  # Check if the response from DB is valid
            except IndexError:
                return {}  # If response is invalid -> return empty entity
            self.__cache.put(key=entity_id, value=results)  # If response is valid - > save entity to cache
        else:
            print(f"Cache hit {self.__cache.index().__str__()}")
        return results

    async def index(self) -> list[dict]:
        """
        This method returns all entities from the repository.
        :return: if the repository is not empty, then it returns a list with entities from it, otherwise it returns [].
        """
        entities_list = await self.__make_query(f"SELECT * FROM {TABLE_NAME}")
        if entities_list is None:
            return []
        return entities_list

    async def list_paginated(self, page: int) -> list[dict]:
        """
        This method returns all entities from the repository page-by-page.
        :param page: page number; starting page is 1.
        :return: if the repository is not empty, then it returns a list with entities from it, otherwise it returns [].
        """
        offset = (page - 1) * PAGE_LIMIT
        entities_list = await self.__make_query(f"SELECT * FROM {TABLE_NAME} LIMIT {PAGE_LIMIT} OFFSET {offset}")
        if entities_list is None:
            return []
        return entities_list

    async def add(self, entity: dict) -> int:
        """
        This method adds a new entity to the repository.
        :param entity: entity with filled parameters.
        :return: if an entity with this id does not exist, then it returns 0, otherwise it returns -1
        """
        keys = self.__format_keys(entity)
        values = self.__format_values(entity)
        if self.get(entity["id"]) == {}:
            await self.__make_query(f"""INSERT INTO {TABLE_NAME} ({keys}) 
                              VALUES ({values}) RETURNING id;""",
                              entity=entity)
            self.__cache.put(entity["id"], entity)
            return 0
        return -1

    async def delete(self, entity_id: int) -> int:
        """
        This method deletes one entity from the repository by id.
        :param entity_id: integer value 'id' of the entity..
        :return: if an entity with this id exists at the time of deletion, then it returns 0, otherwise it returns -1.
        """
        if self.get(entity_id) != {}:  # Check if entity exists in repository
            params = self.get_template(entity_id=entity_id)  # Prepare params for query
            await self.__make_query(f"DELETE FROM {TABLE_NAME} WHERE id = %(id)s RETURNING id;", entity=params)  # Do query
            self.__cache.delete(entity_id)  # Delete entity from cache. It's cheaper than __db.clear()
            return 0
        return -1

    async def update(self, entity: dict) -> int:
        """
        This method updates one entity from the repository by id.
        :param entity: entity with filled parameters.
        :return: if an entity with this id exists, then it updates entity and returns 0, otherwise it returns -1.
        """
        if self.get(entity["id"]) != {}:
            keys = self.__format_keys_no_id(entity)  # Prepare keys for query
            values = self.__format_values_no_id(entity)  # Prepare values for query
            await self.__make_query(f"""UPDATE {TABLE_NAME} 
                                SET {keys} = {values} 
                                WHERE id = %(id)s RETURNING id;""",
                              entity=entity)  # Do query
            self.__cache.delete(entity["id"])  # Delete entity from cache. It's cheaper than updating the cache
            return 0
        return -1

    async def search(self, query: str) -> list[dict]:
        """
        This method returns all entities from the repository.
        :return: if the repository is not empty, then it returns a list with entities from it, otherwise it returns [].
        """
        entities_list = await self.__make_query(f"""SELECT * FROM {TABLE_NAME} WHERE 
                                            to_tsvector(title) @@ to_tsquery(%(query)s);""",
                                          entity={"query": query})
        if entities_list is None:
            return []
        return entities_list


async def main(loop):
    entity = repo.get_template(1, str(1))
    t1 = loop.create_task(repo.add(entity))
    await t1


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    from .repository_factory import RepositoryFactory
    repo = RepositoryFactory.create()

    loop.run_until_complete(main(loop))
    loop.close()
