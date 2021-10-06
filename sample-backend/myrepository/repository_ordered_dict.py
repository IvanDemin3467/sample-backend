from .abstract_repository import AbstractRepository
from collections import OrderedDict

PAGE_LIMIT = 10


class RepositoryOrderedDict(AbstractRepository):
    """
    This class is a simple implementation of repository.
    It stores entities in an ordered dict.
        Documentation says that OrderedDict provides O(1) complexity of read, add and delete.
    The most recently used entity is stored in the bottom of the cache.
        The least recently used - in the head of the cache.
    Entities are stored in the form of entity_id-value, where entity_id is "id" which is int.
        Other params of the entity are stored as dict.
    """
    def __init__(self, options: dict):
        self.__options = options  # Save options
        self.__db = OrderedDict()

    def get(self, entity_id: int) -> dict:
        """
        This method returns one entity by id from the repository.
        :param entity_id: integer value of the entity 'id'.
        :return: if the entity is found in the repository, then it returns the entity, otherwise it returns {}.
        """
        if entity_id in self.__db:
            return self.__db[entity_id]  # Return entity from repository. Time Complexity : O(1)
        return {}

    def index(self) -> list[dict]:
        """
        This method returns all entities from the repository.
        :return: if the repository is not empty, then it returns a list with entities from it, otherwise it returns [].
        """
        entities_list = list(self.__db.values())
        if entities_list is None:
            return []
        return entities_list

    def list_paginated(self, page: int) -> list[dict]:
        """
        This method returns all entities from the repository page-by-page.
        :param page: page number; starting page is 1.
        :return: if the repository is not empty, then it returns a list with entities from it, otherwise it returns [].
        """
        offset = (page - 1) * PAGE_LIMIT
        dict_list = list(self.__db.values())
        entities_list = []
        for i in range(offset, offset+PAGE_LIMIT):
            try:
                entities_list.append(dict_list[i])
            except IndexError:
                break
        if entities_list is None:
            return []
        return entities_list

    def add(self, entity: dict) -> int:
        """
        This method adds a new entity to the repository.
        :param entity: entity with filled parameters.
        :return: if an entity with this id does not exist, then it returns 0, otherwise it returns -1
        """
        key = entity["id"]  # Key to search in repository
        try:
            _ = self.__db[key]  # Check if entity with this id exists in repository. Time Complexity : O(1)
            return -1  # If it exists -> no exception -> return error code -1
        except KeyError:  # If it does not exist -> got exception ->
            self.__db[key] = entity  # Add entity to repository. Time Complexity : O(1)
            return 0  # Return success code 0

    def delete(self, entity_id: int) -> int:
        """
        This method deletes one entity from the repository by id.
        :param entity_id: integer value 'id' of the entity..
        :return: if an entity with this id exists at the time of deletion, then it returns 0, otherwise it returns -1.
        """
        try:
            _ = self.__db[entity_id]  # Check if entity with this id exists in repository. Time Complexity : O(1)
            del self.__db[entity_id]  # If it exists -> no exception -> delete entity. Time Complexity : O(1)
            return -1  # Return success code 0
        except KeyError:  # If it does not exist -> got exception ->
            return 0  # Return error code -1

    def update(self, entity: dict) -> int:
        """
        This method updates one entity from the repository by id.
        :param entity: entity with filled parameters.
        :return: if an entity with this id exists, then it updates entity and returns 0, otherwise it returns -1.
        """
        key = entity["id"]  # Key to search in repository
        try:
            _ = self.__db[key]  # Check if entity with this id exists in repository. Time Complexity : O(1)
            self.__db[key] = entity  # If it exists -> no exception -> update entity. Time Complexity : O(1)
            return -1  # Return success code 0
        except KeyError:  # If it does not exist -> got exception ->
            return 0  # Return error code -1

    def clear(self) -> None:
        """
        This method clears the cache
        @return: None
        """
        self.__db = OrderedDict()

    def search(self, query: str) -> list[dict]:
        """
        This method returns all entities from the repository.
        :return: if the repository is not empty, then it returns a list with entities from it, otherwise it returns [].
        """
        entities_list = list(self.__db.values())
        result = []
        for entity in entities_list:
            if query in entity["title"]:
                result.append(entity)
        return result
