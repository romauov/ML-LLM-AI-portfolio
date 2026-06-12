"""
Чат с ассистентом сайгой

@author Marat Ibatullin
"""
import json
import logging
import requests

from flask import request

from . import blueprint


@blueprint.route('/saiga_chat', methods=['POST'])
def chat():
    """
    Api доступно по url: https://ai.m16.tech/api/saiga_chat
    
    Принимает POST запрос
    Форма json:
        json_data: dict, следующего формата:
    {
        "text": "Привет. Как дела?",
        "temperature": 0.6
    }

    Возвращает: json()
    """
    logger = logging.getLogger("saiga_chat_routes_logger")
    if len(logger.handlers) == 0:
        file_handler = logging.FileHandler("log/saiga_chat_routes_logger.log")
        formatter = logging.Formatter('[%(levelname)-10s] %(asctime)-25s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    request_data = request.get_json()
    url = "{{INTERNAL_HOST}}:8080/saiga_сhat"
    logger.info(json.dumps(request_data, ensure_ascii=False))
    response = requests.post(url, json.dumps(request_data), timeout=100)
    if response.status_code == 200:
        result = response.json()
        logger.info(json.dumps(result, ensure_ascii=False))
        return json.dumps(result, ensure_ascii=False)
    logger.info(response.status_code)
    return response.status_code
