from __future__ import annotations

import json  # to read options from file
import sys  # for repository factory (it creates class by name (string))

import time

# from myfactory import *
from .abstract_repository import AbstractRepository
from .abstract_repository_factory import AbstractRepositoryFactory
from .repository_ram import RepositoryRAM, RepositoryBytearray
from .repository_sql import RepositoryPostgres

OPTIONS_FILE_PATH = "options.json"


class RepositoryFactory(AbstractRepositoryFactory):
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
