"""
Рекомендательный весовой алгоритм

запрос:
{
"axeId": 342
"products": {"Говядина": ["Лопатка", "Язык"]},
"numberOfDays": 90,
"lastMailOpeningDate": "2022-11-08",
"sentToOpenedRelation": 0.5,
"activityLevel": 0.025,
}

ответ:
[{
'email': 'rushan.mkk@gmail.com',
'userId': 281,
'value': 0.028
}]

@author Sergey Vakhrameev
"""
import json
from flask import request
from . import blueprint
from .weight_model import get_users


@blueprint.route('/weight_interest_algorithm', methods=['POST'])
def rec_users():
    """
    Получение пользователей для рассылки
    """
    data = request.get_json()

    if 'axeId' in data and 'sentToOpenedRelation' in data and 'lastMailOpeningDate' in data:
        result = get_users( # использование для подбора пользователей для рассылки
            data['products'],
            data['numberAddresses'],
            data['numberOfDays'],
            data['activityLevel'],
            data['lastMailOpeningDate'],
            data['sentToOpenedRelation'],
            data['axeId'],
        )
    else:
        result = get_users( # использование для подбора пользователей для сокипа
            categories = data['products'],
            number_of_users = data['numberAddresses'],
            number_of_days = data['numberOfDays'],
            min_user_activity_level = data['activityLevel'],
            site = data['site'],
        )

    return json.dumps(result, ensure_ascii=False).encode('utf8')
