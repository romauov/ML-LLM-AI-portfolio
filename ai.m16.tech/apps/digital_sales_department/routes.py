"""
Api для модели LitRecService

@author Sergey Goncharov
"""
import json
from flask import request
from . import blueprint
from .db import active_users
from .user_interest import user_interest_prediction


@blueprint.route('/digital_sales_department/user_interest', methods=['POST'])
def user_interest():
    """
    Получить рекомендации для пользователей
    Запрос - {"users_id": [134, 224]}

    :return: [{'user_id': 123, 'value': 0, 'probability': [0.8942009806632996, -0.4476656913757324]}]

    value 0 - Пользователь не заинтересован в услугах
          1 - Пользователь заинтересован в услугах для продавцов
    """
    data = request.get_json()
    users_id = data['users_id']

    result = user_interest_prediction(users_id)

    return json.dumps(result, ensure_ascii=False).encode('utf8')


@blueprint.route('/digital_sales_department/user_interest_active', methods=['POST'])
def user_interest_active():
    """
    Получить рекомендации для активных пользователей
    :return: [{
    'user_id': 123,
    'value': 0,
    'probability': [0.8942009806632996, -0.4476656913757324],
    'info': {'user_id', 'firstname', 'lastname', 'login'}
    }]

    value 0 - Пользователь не заинтересован в услугах
          1 - Пользователь заинтересован в услугах для продавцов
    """
    data = request.get_json()
    activity = data['activity']
    users = active_users(activity)

    users_id = [user[0] for user in users]

    result = user_interest_prediction(users_id)

    users = {user[0]: {
        'firstname': user[1],
        'lastname': user[2],
        'email': user[3],
        'date': user[4].strftime("%Y-%m-%d")
    } for user in users}

    result = list(filter(lambda it: it['value'] > 0, result))

    for index, item in enumerate(result):
        result[index]['info'] = users[item['user_id']]

    return json.dumps(result, ensure_ascii=False).encode('utf8')
