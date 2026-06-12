"""
Валидатора ответов 

@author Dmitry Abramov
"""
import json
import logging

from flask import request

from . import blueprint
from .recommender import ReccomendationPipeline

model = ReccomendationPipeline()

# Логирование
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/knn_recommendations_logs.log", mode='a')
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)


@blueprint.route('/knn_recommenations', methods=['POST'])
def rec():
    """
    Api доступно по url: https://ai.m16.tech/api/knn_recommenations

    Принимает: json({"product": "Говядина мясо",
                     "number_of_users": 1})

    Возвращает: json({"emails": ['@email'],
                      "userIds": [1], 
                      "tsop_id" 10})
    Возвращаемые ошибки:
    Если не удалось найти пользователей по type1:
        json({"error": "type1='Собачело' не найден"})
    """
    request_data = request.get_json()

    result = model.pipeline(**request_data)

    if isinstance(result, dict):
        return json.dumps(result, ensure_ascii=False)
    log_ids = [str(id) for id in result[1]]
    log = f"{request_data['product']} " + f"tsop_id: {request_data['tsop_id']} " + "userIds: " + " ".join(log_ids)
    logger.info(log)
    return json.dumps({'emails': result[0],
                       'userIds': result[1],
                       'note': result[2]}, 
                       ensure_ascii=False)
