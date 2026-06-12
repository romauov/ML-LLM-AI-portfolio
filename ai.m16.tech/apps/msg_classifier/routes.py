"""
API сервиса для квалификации входящих сообщений

@author Sergei Romanov
"""
import json
import logging
from flask import request
from .msg_classifier_merged import classify_merged
from .msg_classifier_giga import classify_giga
from .msg_classifier_gpt import classify_gpt
from . import blueprint

# Логирование
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/msg_classifier_logs.log", mode='a')
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)


@blueprint.route('/msg_classifier', methods=['POST'])
def get_reply():
    """
    Получение пользователей для рекомендации продукта
    json
    {
    "msg": "добрый день можно получит прайс лист"
    }
    """
    query = request.get_json()
    text = query['text']
    try:
        if query['method'] == 'chat_gpt':
            result = classify_gpt(text)
        elif query['method'] == 'giga_chat':
            result = classify_giga(text)
        elif query['method'] == 'merged':
            result = classify_merged(text)
        else:
            result = {'method': 'no method provided',
                      'error': 'выберите допустимый способ квалификации: "chat_gpt", "giga_chat" или "merged"'}
    except KeyError:
        result = {'method': 'no method provided',
                  'error': 'выберите допустимый способ квалификации: "chat_gpt", "giga_chat" или "merged"'}

    try:
        log = f"text: {query['text']}, method: {query['method']} " + f"msg_classes: {result['msg_classes']}"
    except KeyError:
        log  = f"text: {query['text']}, method: {result['method']} " + f"error: {result['error']}"
    logger.info(log)

    return json.dumps(result, ensure_ascii=False)
