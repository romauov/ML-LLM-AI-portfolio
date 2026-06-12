"""
API сервиса автоматического ответа пользователю

@author Sergei Romanov
"""
# import asyncio
import json
import logging
from flask import request
from chat_helper.chat_helper import run_conversation, clear_history_for_chat
from . import blueprint
# Логирование
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler("log/chat_helper_logs.log", mode='a')
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

@blueprint.route('/chat_helper', methods=['POST'])
def get_reply():
    """
    Получение пользователей для рекомендации продукта
    json
    {
    "user_promt": "нужны цены на вырезку",
    "table_id": "12Fj1RcAr0yB6PLtq_S6MH27I0wVV0Fgo8_QkACrovvo",
    "text_id": "1L32jhOaPfgOwIRSj5FPy1JxCQ22T1cBlR6IStDGhDGE",
    "from_id": "100500" 
    }
    """
    query = request.get_json()
    # result = asyncio.run(run_conversation(**query))
    result = run_conversation(**query)
    res = json.loads(result)
    try:
        log = f"user_id: {query['from_id']}, \
            message: {query['user_promt']}, reply: {res['reply']}, charge: {res['charge']}"
    except KeyError:
        log = f"message: {query['user_promt']}, reply: {res['reply']}, charge: {res['charge']}"
    logger.info(log)
    return result

@blueprint.route('/chat_helper_clear', methods=['POST'])
def clear_history():
    """
    очистка истории сообщений
    json
    {
    "from_id": "100500" 
    }
    """
    query = request.get_json()
    clear_history_for_chat(**query)
