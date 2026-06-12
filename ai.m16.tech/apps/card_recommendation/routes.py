"""
Рекомендации на основе портрета пользователя 

@author Marat Ibatullin
"""
import json
import logging

from flask import request

from .cards_backend import index_init
from . import blueprint

@blueprint.route("/card_recommendations", methods=['POST'])
def card_recommendations():
    """
    Получения рекомендаций
    
    Pipeline состоит из нескольких основных компонентов:
            1. Векторизация суммаризированной карточки
            2. Получение пользователей и эмбеддингов полученных из их карточек
            3. Обучение faiss-индекса считанными эмбеддингами
            4. Агрегация данных

    Возвращается список(срез) email пользователей

    json example'{"tsop_id": "51",
                  "number_of_users": 100,
                  "site":"meatinfo",
                  "user_portrait":
                    "{'prods': 'Форель охлажденная', 
                      'info': ' Компания занимается переработкой рыбы, переработчик.,
                      'position': 'менеджер по закупкам, руководитель отдела закупок.'}"}'
    """
    request_data = request.get_json()
    number_of_users = request_data['number_of_users']
    user_portrait = request_data['user_portrait']
    site = request_data['site']
    tsop_id = request_data['tsop_id']

    logger = logging.getLogger("card_rec_routes_logger")
    if len(logger.handlers) == 0:
        file_handler = logging.FileHandler("log/card_rec_routes_logger.log", mode='a')
        formatter = logging.Formatter('[%(levelname)-10s] %(asctime)-25s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    reccomend = index_init(user_portrait, site, number_of_users, tsop_id)
    str_ids = ','.join(map(str, reccomend['Id']))

    logger.info("Портрет пользователя: %s | Количество email: %s| Ответ модели: %s | tsop id: %s",
                user_portrait, number_of_users, str_ids, tsop_id)
    del reccomend['Id']

    return json.dumps(reccomend)
