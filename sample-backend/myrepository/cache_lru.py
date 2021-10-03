from collections import OrderedDict


class CacheLRU:
    """
    This class is a simple implementation of Least Recent Used (LRU) cache.
    It stores entities in an ordered dict.
        Documentation says that OrderedDict provides O(1) complexity of read, add and delete.
    The most recently used entity is stored in the bottom of the cache.
        The least recently used - in the head of the cache.
    Entities are stored in the form of key-value, where key is "id" which is int.
        Other params of the entity are stored as dict.
    """
    def __init__(self, maxsize=128):
        self.__max_size = maxsize
        self.__cache = OrderedDict()

    def put(self, key: int, value: dict) -> None:
        """
        This method adds new entity to the bottom of the cache
        @param key: integer id of entity
        @param value: dict of properties of entity
        @return: None
        """
        self.__cache[key] = value  # Add entity to cache
        self.__cache.move_to_end(key)  # Not necessary as new element is auto added to the end. Time Complexity : O(1)
        if len(self.__cache) > self.__max_size:  # Check if we are out of free space in cache
            self.__cache.popitem(last=False)  # Remove least recently used element (from head of the cache)

    def get(self, key: int) -> dict or int:
        """
        This method retrieves entity from the cache.
            If entity exists in cache then makes it least recently used (moves to the bottom of the cache)
        @param key:  integer id of entity
        @return: dict of properties of entity (if cache hit) or -1 (if cache miss)
        """
        if key not in self.__cache:
            return -1
        else:
            self.__cache.move_to_end(key)  # Queried entity become least recent used. Time Complexity : O(1)
            return self.__cache[key]  # Return entity from cache

    def clear(self) -> None:
        """
        This method clears the cache
        @return: None
        """
        self.__cache = OrderedDict()

    def delete(self, key: int) -> None:
        """
        This method deletes one entity from cache
        @param key: integer value if an entity_id
        @return: None
        """
        try:
            self.__cache.pop(key)
        except KeyError:
            pass

    def index(self) -> OrderedDict:
        """
        This method returns all entities in the cache
        @return: all entities i an OrderedDict
        """
        return self.__cache
