"""
Валидатора ответов 

@author Marat Ibatullin
"""
import json
import logging

from flask import request

from .recommender_bert import recommendation, recommendation_polars
from . import blueprint


@blueprint.route("/bert_recommendations", methods=['POST'])
def temp():
    """
    Получения рекомендаций
    
   Pipeline состоит из нескольких основных компонентов:
            1. Считываются Эмбеддинги в формате np.array .astype('float32')
            2. Обучаются движки поиска похожих векторов
            3. Создается список staff_to_found - тексты похожих объявлений и поисковых запросов
            4. Создаются рекомендации со следующими условиями
                a. Пользователи являются покупателями
                b. Текст объявления или поисковый запрос совпадает с одним из staff_to_found
                c. Покупатель не просматривает свое же объявление

    Возвращается список(срез) ID пользователей в порядке:(первый в списвке - последней взаимодействующий 
    с интересующими нас объявлениями или поисковыми запросами)  

    json example'{"context": "Продам: жир топленый свиной оптовые продажи", "number_of_users": 2, 
    "site":"meatinfo", "search": "жир топленый свиной"}'

    """
    reccomend={}
    request_data = request.get_json()
    context = request_data['context']
    search = request_data['search']
    number_of_users = request_data['number_of_users']
    site = request_data['site']
    tsop_id = request_data['tsop_id']

    logger = logging.getLogger("bert_rec_routes_logger")
    if len(logger.handlers) == 0:
        file_handler = logging.FileHandler("log/bert_rec_routes_log.log", mode='a')
        formatter = logging.Formatter('[%(levelname)-10s] %(asctime)-25s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    reccomend = recommendation(context, search, number_of_users, site, tsop_id)
    str_ids = ','.join(map(str, reccomend['Id']))
    logger.info("Текст объявления: %s | Поисковый запрос: %s | Количество email: %s| Ответ модели: %s | tsop id: %s",
                context, search, number_of_users, str_ids, tsop_id)
    del reccomend['Id']
    return json.dumps(reccomend)

@blueprint.route("/bert_recommendations_polars", methods=['POST'])
def test():
    """
    Получения рекомендаций
    
   Pipeline состоит из нескольких основных компонентов:
            1. Считываются Эмбеддинги в формате np.array .astype('float32')
            2. Обучаются движки поиска похожих векторов
            3. Создается список staff_to_found - тексты похожих объявлений и поисковых запросов
            4. Создаются рекомендации со следующими условиями
                a. Пользователи являются покупателями
                b. Текст объявления или поисковый запрос совпадает с одним из staff_to_found
                c. Покупатель не просматривает свое же объявление

    Возвращается список(срез) ID пользователей в порядке:(первый в списвке - последней взаимодействующий 
    с интересующими нас объявлениями или поисковыми запросами)  

    json example'{"context": "Продам: жир топленый свиной оптовые продажи", "number_of_users": 2, 
    "site":"meatinfo", "search": "жир топленый свиной"}'

    """
    reccomend = {}
    request_data = request.get_json()
    context = request_data['context']
    search = request_data['search']
    number_of_users = request_data['number_of_users']
    site = request_data['site']
    tsop_id = request_data['tsop_id']

    logger = logging.getLogger("bert_rec_routes_logger")
    if len(logger.handlers) == 0:
        file_handler = logging.FileHandler("log/bert_rec_routes_log.log", mode='a')
        formatter = logging.Formatter('[%(levelname)-10s] %(asctime)-25s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    reccomend = recommendation_polars(context, search, number_of_users, site, tsop_id)
    str_ids = ','.join(map(str, reccomend['Id']))
    logger.info("Текст объявления: %s | Поисковый запрос: %s | Количество email: %s| Ответ модели: %s | tsop id: %s",
                context, search, number_of_users, str_ids, tsop_id)
    del reccomend['Id']
    return json.dumps(reccomend)
