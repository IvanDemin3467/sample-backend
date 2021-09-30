from __future__ import annotations
from abc import ABC, abstractmethod


# Factory for entities start
class TypeChecker:
    """
    Это дескриптор, проверяющий принадлежность значения переменной инстанса с именем name к типу value_type
    """
    def __init__(self, name, value_type):
        self.name = name
        self.value_type = value_type

    def __set__(self, instance, value):
        if isinstance(value, self.value_type):
            instance.__dict__[self.name] = value
        else:
            raise TypeError(f"'{self.name}' {value} must be {self.value_type}")

    def __get__(self, instance, class_):
        return instance.__dict__[self.name]


class DictChecker:
    """
    Это дескриптор, проверяющий принадлежность значения переменной инстанса с именем name к типу value_type
    """
    def __init__(self, dict_name, key_name):
        self.dict_name = dict_name
        self.key_name = key_name

    def __set__(self, instance, dict_value):
        if isinstance(dict_value, dict):
            if self.key_name in dict_value:
                instance.__dict__[self.dict_name] = dict_value
            else:
                raise TypeError(f"User init error. Key '{self.key_name}' must be in {self.dict_name} dictionary")
        else:
            raise TypeError(f"User init error. Given {self.dict_name} structure must be {dict}")

    def __get__(self, instance, class_):
        return instance.__dict__[self.dict_name]


class Entity(ABC):
    """
    Абстрактная сущность, от которой будут наследоваться конкретные сущности, такие как User
        Сущности будут создаваться фабрикой AbstractFactory. Храниться они будут в репозитории AbstractRepository
    Определяет конструктор по умолчанию, в котором сохраняются id сущности и словарь её параметров
    Метод get_dict() должен возвращать словарь, в котором записаны все параметры сущности, включая и её id.
        Он нужен, чтобы возвращать представление сущности через jsonify()
    Добавлена небольшая оптимизация при помощи __slots__. Расход памяти должен уменьшиться
    """
    __slots__ = ['id', 'properties']
    id_checker = TypeChecker("id", int)
    properties_checker = TypeChecker("properties", dict)

    def __init__(self, entity_id: int, properties: dict) -> None:
        self.id = entity_id
        self.properties = properties

    @abstractmethod
    def get_dict(self) -> dict:
        raise NotImplementedError


class User(Entity):
    """
    Конкретный класс, реализующий абстракцию Entity. Предназначен для хранения id и ФИО пользователей в репозитории
    """
    id = TypeChecker("id", int)
    properties = DictChecker("properties", "title")

    def __init__(self, user_id: int, properties: dict) -> None:
        super().__init__(user_id, properties)

    def get_dict(self) -> dict:
        """
        Преобразовывает параметры сущности User в вид, подходящий для функции jsonify()
        :return: словарь с параметрами сущности User, включая и id
        """
        result = {"id": self.id}
        result.update(self.properties)
        return result


class AbstractFactory(ABC):
    """
    Интерфейс Абстрактной фабрики для создания сущностей Entity.
    Определяет абстрактные методы:
        create() для создания сущности с переданными параметрами;
        create_empty() классовый метод для создания пустой сущности
            для возврата из репозитория при ошибочных переданных параметрах
        get_factory_name() для возвращения имени фабрики (может потребоваться, чтобы дать имя таблице в базе данных)
    Определяет классовую переменную
        __empty_entity, в которой хранится инстанс пустой сущности (чтобы не создавать многократно)
    """
    __empty_entity: Entity

    @property
    @abstractmethod
    def empty_entity(self) -> Entity:
        """
        Дескриптор, который делает классовое свойство empty_entity приватным (readonly)
        :return: возвращает содержимое __empty_entity
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, entity_id: int, properties: dict) -> Entity:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def create_empty(cls) -> Entity:
        raise NotImplementedError

    @abstractmethod
    def get_factory_name(self) -> str:
        raise NotImplementedError


class UserFactory(AbstractFactory):
    """
    Конкретная реализация абстрактный фабрики. Предназначена для работы с сущностями User
        create() - создаёт пользователя по переданным параметрам. Проверяет валидность параметров
        get_factory_name() - возвращает имя фабрики "users" (может быть использовано в базе данных)
        empty_entity
    """

    def __init__(self):
        """
        Инициализирует классовую переменную __empty_entity.
        Она используется для возвращения несуществующих сущностей из фабрики или из репозитория
        """
        UserFactory.create_empty()

    @property
    def empty_entity(self) -> Entity:
        """
        Дескриптор, который делает классовое свойство empty_entity приватным (readonly)
        :return: возвращает содержимое __empty_entity, то есть, пустую сущность User
        """
        return self.__empty_entity

    def create(self, user_id: int, properties: dict) -> Entity:
        """
        Создаёт сущность User в соответствии с переданными параметрами
        :param user_id: целочисленное значение id пользователя
        :param properties: строковое значение ФИО пользователя
        :return: объект User с заполненными параметрами, либо пустой User, если переданы неверные параметры
        """
        entity = UserFactory.__empty_entity
        try:
            entity = User(user_id, properties)
        except TypeError as err:
            print(err)
        return entity

    @classmethod
    def create_empty(cls) -> Entity:
        """
        Классовый метод, который запускается при инициализации инстанса фабрики
        Создаёт сущность User с пустым ФИО и id=-1 и сохраняет его в классовую переменную __empty_entity.
            Такой id служит признаком несуществующей сущности
            Эта переменная позже делается неизменяемой
            Переменная сделана классовой, чтобы не создавать многократно
        :return: объект User с пустым ФИО и id=-1
        """
        entity = User(-1, {"title": ""})
        cls.__empty_entity = entity
        return entity

    def get_factory_name(self) -> str:
        """
        Позволяет узнать имя фабрики. В данном случае это "users"
        :return: строковое значение имени фабрики
        """
        return "users"


if __name__ == "__main__":
    """
    Небольшой тест дескрипторов TypeChecker и DictChecker
    """
    factory = UserFactory()
    print("ID строковый вместо целочисленного")
    user = factory.create("1", {"title": "des"})
    result = user.get_dict()
    print(result)
    assert result == {'id': -1, 'title': ''}

    print("\nПередан список свойств вместо словаря")
    user = factory.create(1, ["title", "des"])
    result = user.get_dict()
    print(result)
    assert result == {'id': -1, 'title': ''}

    print("\nПередан словарь с отсутствующим ключом 'title'")
    user = factory.create(1, {"tit": "des"})
    result = user.get_dict()
    print(result)
    assert result == {'id': -1, 'title': ''}

    print("\nВсе параметры переданы верно")
    user = factory.create(1, {"title": "des"})
    result = user.get_dict()
    print(result)
    assert result == {'id': 1, 'title': 'des'}

    """
    Тест __slots__
    """

    print("\nПопытка установки свойства инстанса, не входящего в __slots__. Не должно ничего измениться")
    user.property = "sample-property"
    result = user.get_dict()
    print(result)
    assert result == {'id': 1, 'title': 'des'}

    """
    Тест приватности свойства empty_entity
    """

    print("\nПолучение empty_entity")
    empty = factory.empty_entity
    result = user.get_dict()
    print(result)
    assert result == {'id': 1, 'title': 'des'}

    print("\nУстановка непустого значения empty_entity и повторный запрос на получение")
    try:
        factory.empty_entity = user
    except AttributeError as e:
        print(e)
    empty = factory.empty_entity
    result = empty.get_dict()
    print(result)
    assert result == {'id': -1, 'title': ''}

    print("\nПопытка непосредственного обращения к приватному свойству")
    try:
        empty = factory.__empty_entity
        print(empty.get_dict())
    except AttributeError as e:
        assert str(e) == "'UserFactory' object has no attribute '__empty_entity'"
        print(e)

    print("\nПопытка непосредственного изменения приватного свойства приводит к созданию runtime приватного свойства")
    print("но не изменяет настоящее классовое свойство")
    try:
        factory.__empty_entity = user
        empty = factory.__empty_entity
        print(empty.get_dict())
        result = factory.empty_entity.get_dict()
        print(result)
        assert result == {'id': -1, 'title': ''}
    except AttributeError as e:
        print(e)
