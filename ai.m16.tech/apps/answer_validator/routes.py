"""
Квалификатор ответов 

@author Dmitry Abramov
"""
import logging

from flask import request, jsonify

from . import blueprint
from .classifier import AnswerValidator

model = AnswerValidator()
model()

# Логирование
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/answer_validator_logs.log", mode='a')
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

@blueprint.route('/answer_validator', methods=['POST'])
def validate():
    """
    Api доступно по url: https://ai.m16.tech/api/answer_validator

    Принимает json({"text": "Тут сообщение"})

    Возвращает json({"class": "спам", "class_name": 5})
    """
    request_data = request.get_json()

    result = model.predict(request_data['text'])

    log = f"{request_data['text']} class: {result['class']}"
    logger.info(log)

    return jsonify(result)
