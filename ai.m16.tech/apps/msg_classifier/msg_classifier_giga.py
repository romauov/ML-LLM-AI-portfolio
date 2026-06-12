"""
Сервис для квалификации входящих сообщений заданным набором ярлыков с помощью Giga Chat

example_input = 'добрый день можно получит прайс лист'

example_output = {"msg_classes": ['запрос прайса']}
    
@author Sergei Romanov
"""
import json
# pylint: disable=no-name-in-module
from langchain.chat_models import GigaChat
from langchain.schema import HumanMessage, SystemMessage
from gigachat import exceptions

from . import classifier_promt, GIGA_CHAT_KEY

chat = GigaChat(credentials=GIGA_CHAT_KEY, verify_ssl_certs=False, model='GigaChat-Plus',
                temperature=0.05, scope="GIGACHAT_API_CORP")



def classify_giga(text):
    """функция для присваивания ярлыков, входящему сообщению

    Args:
        msg (str): сообщения пользователя

    Returns:
        lst: список ярлыков
    """
    try:
        messages = [SystemMessage(content=classifier_promt)]
        messages.append(HumanMessage(content=json.dumps(text, ensure_ascii=False)))
        result = chat(messages).content
        if result.startswith('['):
            result = result[1:-1]
        result = result.split(', ')
        result = [i[1:-1] if i.startswith("'") or i.startswith("\"") else i for i in result]
        return {"msg_classes": result}
    except exceptions.ResponseError as e:
        return {"error": f"Произошла ошибка при обращении к API GigaChat: {e}, повторите запрос"}
     