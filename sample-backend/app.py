from __future__ import annotations

from flask import Flask, jsonify, request

from myrepository.repository_factory import RepositoryFactory

"""
Начало работы REST API сервиса
"""
app = Flask(__name__)  # инициализация объекта, с которым сможет работать WSGI сервер
app.config['SECRET_KEY'] = 'gh5ng843bh68hfi4nfc6h3ndh4xc53b56lk89gm4bf2gc6ehm'  # произвольная случайная длинная строка
repo = RepositoryFactory.create()  # инициализация репозитория


@app.route('/user/<int:entity_id>', methods=['GET'])
def get_entity(entity_id: int) -> (str, int):
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/user/2
    :param entity_id: целочисленное значение id пользователя
    :return: если пользователь найден в базе, то возвращает json с данными пользователя и код 200,
             иначе возвращает код 404
             Формат возвращаемого значения: {"id": entity_id, "title": title}
    """
    result = repo.get(entity_id)
    if result == {}:
        return "Rejected. No entity with id=" + str(entity_id), 404
    return jsonify(result), 200


@app.route('/user', methods=['GET'])
def list_entities() -> (str, int):
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/users
    :return: если база не пуста, то возвращает json с данными пользователей и код 200,
             иначе возвращает код 404
             Формат возвращаемого значения: [{"id": user_id1, "title": title1}, {"id": user_id2, "title": title2}]
    """
    entities_list = repo.index()
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
    # new_entity = {'title': title, 'id': entity_id}
    new_entity = repo.get_template(entity_id=entity_id, par1=title)
    if repo.add(new_entity) == -1:
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
    # new_entity = {'title': title, 'id': entity_id}
    new_entity = repo.get_template(entity_id=entity_id, par1=title)
    result = repo.update(new_entity)
    if result == -1:
        return "Rejected. No entity with id=" + str(entity_id), 404
    return 'Success. Entity updated', 204


@app.route('/user/search/', methods=['GET'])
def search_entity() -> (str, int):
    """
    Точка входа для запроса на получение записи пользователя по id. Пример запроса:
    curl http://localhost:80/users
    :return: если база не пуста, то возвращает json с данными пользователей и код 200,
        иначе возвращает код 404
        Формат возвращаемого значения: [{"id": user_id1, "title": title1}, {"id": user_id2, "title": title2}]
    """
    query = request.args.get('query')
    entities_list = repo.search(query)
    if not entities_list:
        return "Nothing found", 404
    return jsonify(entities_list), 200


if __name__ == '__main__':
    """
    Тестовый запуск сервиса. Активируется только при непосредственном запуске приложения.
    При запуске через WSGI-сервер этот блок игнорируется
    """

    # Main test
    for i in range(1, 12):
        entity = repo.get_template(i, str(i))
        repo.add(entity)
    print(repo.list_paginated(2))

    entity = repo.get_template(1, "123")
    repo.update(entity)
    print(repo.index())
    
    for i in range(1, 5):
        ent = repo.get_template(i, str(i))
        repo.get(i)  # Cache miss expected
        repo.get(i)  # Cache hit expected

    print(repo.search("2"))

    for i in range(12):
        repo.delete(i)
    print(repo.index())

    # Cache test
    """for i in range(1, 5):
        ent = repo.get_template(i, str(i))
        repo.add(ent)
    print(repo.index())

    for i in range(1, 5):
        ent = repo.get_template(i, str(i))
        repo.get(i)  # Cache miss expected
        repo.get(i)  # Cache hit expected

    for i in range(1, 5):
        repo.delete(i)
    print(repo.index())"""

    app.run(host="127.0.0.1", port=80)
