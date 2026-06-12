"""
Валидатор имен
"""
import json

from flask import request

from . import name_blueprint, surname_blueprint
from .classifier import NameClassifier

model = NameClassifier()
model.init_data()


@name_blueprint.route('/name_classifier', methods=['GET'])
def name_predict():
    """
    Валидатор имен

    :return:
    {"name": "dsfdsf", "date": "y-m-d, H:M:S", "label": 0}
    """
    # Получение данных
    name = request.args.get('name', type=str)

    # Если имя отсутствует, возвращается информация об ошибке
    if not name:
        return json.dumps({'error': 'Имя не введено'},
                          ensure_ascii=False)

    # Предсказание
    try:
        output = model.predict_name(name)
        json_array = json.dumps(output, ensure_ascii=False)
    except KeyError:
        json_array = json.dumps({'error': 'Введен недопустимый символ'},
                                ensure_ascii=False)
    # Возвращение результата
    return json_array


@surname_blueprint.route('/surname_classifier', methods=['GET'])
def surname_predict():
    """
    Валидатор фамилий

    :return:
    """
    # Получение данных
    name = request.args.get('name', type=str)

    # Если имя отсутствует, возвращается информация об ошибке
    if not name:
        return json.dumps({'error': 'Фамилия не введена'},
                          ensure_ascii=False)

    # Предсказание
    try:
        output = model.predict_surname(name)
        json_array = json.dumps(output, ensure_ascii=False)
    except KeyError:
        json_array = json.dumps({'error': 'Введен недопустимый символ'},
                                ensure_ascii=False)
    # Возвращение результата
    return json_array
