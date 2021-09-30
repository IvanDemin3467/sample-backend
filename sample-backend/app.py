from __future__ import annotations
import uuid

from flask import Flask, jsonify, request

from myrepository import *

BOOKS = [
    {
        'id': uuid.uuid4().hex,
        'title': 'On the Road',
        'author': 'Jack Kerouac',
        'read': True
    },
    {
        'id': uuid.uuid4().hex,
        'title': 'Harry Potter and the Philosopher\'s Stone',
        'author': 'J. K. Rowling',
        'read': False
    },
    {
        'id': uuid.uuid4().hex,
        'title': 'Green Eggs and Ham',
        'author': 'Dr. Seuss',
        'read': True
    }
]

TABLE = [
    {
        'date': '22.09.2021',
        'title': 'Apples',
        'amount': '12',
        'distance': '125'
    },
    {
        'date': '21.09.2021',
        'title': 'Oranges',
        'amount': '14',
        'distance': '135'
    },
    {
        'date': '20.09.2021',
        'title': 'Bananas',
        'amount': '15',
        'distance': '168'
    }
]

# configuration
DEBUG = True

"""
Начало работы REST API сервиса
"""
app = Flask(__name__)  # инициализация объекта, с которым сможет работать WSGI сервер
app.config['SECRET_KEY'] = 'gh5ng843bh68hfi4nfc6h3ndh4xc53b56lk89gm4bf2gc6ehm'  # произвольная случайная длинная строка
repo = RepositoryCreator.create()  # инициализация репозитория


@app.route('/user/<int:entity_id>', methods=['GET'])
def get_entity(entity_id: int) -> (str, int):
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/user/2
    :param entity_id: целочисленное значение id пользователя
    :return: если пользователь найден в базе, то возвращает json с данными пользователя и код 200,
             иначе возвращает код 404
             Формат возвращаемого значения: {"id": user_id, "title": title}
    """
    entity = repo.get(entity_id)
    if entity == {}:
        return "Rejected. No entity with id=" + str(entity_id), 404
    return jsonify(entity), 200


@app.route('/user', methods=['GET'])
def list_entities() -> (str, int):
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/users
    :return: если база не пуста, то возвращает json с данными пользователей и код 200,
             иначе возвращает код 404
             Формат возвращаемого значения: [{"id": user_id1, "title": title1}, {"id": user_id2, "title": title2}]
    """
    entities_list = repo.list()
    if not entities_list:
        return "Rejected. DB is empty", 404
    return jsonify(entities_list), 200


@app.route('/user/<int:entity_id>', methods=['POST'])
def add_entity(entity_id: int) -> (str, int):
    """
    Точка входа для запроса на добавление записи пользователя по id. Пример запроса:
    curl -X POST http://localhost:80/user/3?title=Mikhail%20Vasilevich%20Lomonosov
    :param entity_id: целочисленное значение id пользователя
    :аргумент запроса title: строковое значение ФИО пользователя
    :return: если пользователь существует в базе, то не создаёт пользователя и возвращает код 422,
             иначе создаёт и возвращает код 204
    """
    title = request.args.get('title')
    entity = {'title': title, 'id': entity_id}
    if repo.add(entity) == -1:
        return "Rejected. User with id=" + str(entity_id) + " already exists", 422
    return 'Success. User created', 204


@app.route('/user/<int:entity_id>', methods=['DELETE'])
def del_entity(entity_id: int) -> (str, int):
    """
    Точка входа для запроса на удаление записи пользователя по id. Пример запроса:
    curl -X DELETE http://localhost:80/user/3
    :param entity_id: целочисленное значение id пользователя
    :return: если пользователь не существует в базе, то возвращает код 422,
             иначе удаляет его и возвращает код 204
    """
    if repo.delete(entity_id) == -1:
        return "Rejected. No user with id=" + str(entity_id), 404
    return 'Success. User deleted', 204


@app.route('/user/<int:entity_id>', methods=['PATCH'])
def upd_entity(entity_id: int) -> (str, int):
    """
    Точка входа для запроса на изменение записи пользователя по id. Пример запроса:
    curl -X PATCH http://localhost:80/user/3?title=Aleksandr%20Sergeevich%20Pushkin
    :param entity_id: целочисленное значение id пользователя
    :аргумент запроса title: строковое значение ФИО пользователя
    :return: если пользователь не существует в базе, то возвращает код 422,
             иначе изменяет его данные и возвращает код 204
    """
    title = request.args.get('title')
    entity = {'title': title, 'id': entity_id}
    result = repo.update(entity)
    if result == -1:
        return "Rejected. No user with id=" + str(entity_id), 404
    return 'Success. User updated', 204


if __name__ == '__main__':
    """
    Тестовый запуск сервиса. Активируется только при непосредственном запуске приложения.
    При запуске через WSGI-сервер этот блок игнорируется
    """

    entity = repo.get_template(1, "qwe")
    '''entity = {'id': 1,
              'title': 'Y Combinator',
              'url': 'http://ycombinator.com',
              'created_at': '2006-10-09T18:21:51.000Z',
              'points': 57,
              'num_comments': 0}'''
    repo.add(entity)
    print(repo.get(1))
    entity = repo.get_template(3, "rty")
    '''entity = {'id': 2,
              'title': 'Build your own React',
              'url': 'https://pomb.us/build-your-own-react/',
              'created_at': '2019-11-13T18:21:51.000Z',
              'points': 1478,
              'num_comments': 108}'''
    repo.add(entity)
    print(repo.list())

    repo.delete(1)
    print(repo.list())

    entity = repo.get_template(2, "123")
    repo.update(entity)
    print(repo.list())

    repo.delete(2)
    print(repo.list())

    app.run(host="127.0.0.1", port=80)
