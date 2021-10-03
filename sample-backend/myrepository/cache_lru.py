from collections import OrderedDict


class CacheLRU:
    """
    This class is a simple implementation of Least Recent Used (LRU) cache.
    It stores entities in an ordered dict, which provides O(1) complexity of reading.
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
        self.__cache[key] = value
        self.__cache.move_to_end(key)
        if len(self.__cache) > self.__max_size:
            self.__cache.popitem(last=False)
