"""
Модель продавец покупатель
@author Dmitry Abramov
"""
import json

from flask import request

from . import blueprint
from .role_classifier import main



@blueprint.route('/buyers-users', methods=['POST'])
def rec_users():
    """
    Модель продавец - покупатель
    запрос:
    {
        "products": ["Говядина"],
        "date_period": 90,
        "number_of_users": 200,
    }
    #
    ответ:
    [{
        'email': 'rushan.mkk@gmail.com'
    }]
    """
    data = request.get_json()

    result = main(
        product=data['products'],
        date_period=data['datePeriod'],
        number_of_users=data['numberOfUsers'],
    )

    return json.dumps(result, ensure_ascii=False).encode('utf8')
