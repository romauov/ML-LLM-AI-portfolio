"""
API сервиса для создания карточки пользователя

@author Sergei Romanov
"""
import json
from flask import request

from .user_card import create_user_card
from .user_json import get_company_data, get_user_data
from . import blueprint

@blueprint.route('/user_profile', methods=['POST'])
def get_user_card():
    """
    Получение получение карточки пользователя
    
    input_exapmle = {'site': "meatinfo", 'user_id': 228618}
    
    example_out_put = {"user_card": user_card.md}
    """
    query = request.get_json()
    result = create_user_card(**query)
    return json.dumps(result, ensure_ascii=False)

@blueprint.route('/user_profile_user_json', methods=['POST'])
def get_user_json():
    """
    Получение данных пользователя
    
    input_exapmle = {'site': "meatinfo", 'user_id': 228618}
    
    example_out_put = {
        "activity": {
            "user_activity": "active",
            "details": []
            },
            "product_action": {
                "sale": {
                    "date_start": "2024-01-01T09:10:15",
                    "date_end": "2024-05-01T11:38:07",
                    "details": []
                    },
                    "buy": {
                        "date_start": "2024-01-01T12:18:38",
                        "date_end": "2024-05-01T16:09:44",
                        "details": []
                        }
                        },
                        "tradeboard_view": {
                            "date_start": "2024-01-01T12:18:38",
                            "date_end": "2024-05-01T16:09:44",
                            "count_all": 30,
                            "sale": {
                                "count": 20",
                                "products": [],
                                "regions": []
                                },
                                "buy": {
                                    "count": 10,
                                    "products": [],
                                    "regions": []
                                    }
                                    }
                                    }
                                    
    """
    query = request.get_json()
    result = get_user_data(**query)
    return json.dumps(result, ensure_ascii=False)

@blueprint.route('/user_profile_company_json', methods=['POST'])
def get_company_json():
    """
    Получение данных пользователя
    
    input_exapmle = {'site': "meatinfo", 'company_id': 163687}
    
    example_out_put = {
        "last_trade": [
            {
                "id": "unsigned int",
                "date": "string(YYYY-MM-DDTHH:ii:ss)",
                "title": "string"
                }
                ],
                "employees": [
                    {...}
                    ]
                    }
    """
    query = request.get_json()
    result = get_company_data(**query)
    return json.dumps(result, ensure_ascii=False)
