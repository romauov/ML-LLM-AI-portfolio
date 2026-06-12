"""
Сервис для квалификации входящих сообщений заданным набором ярлыков с помощью Chat GPT и Giga Chat

example_input = 'добрый день можно получит прайс лист'

example_output = {"msg_classes": ['запрос прайса']}
    
@author Sergei Romanov
"""
import json
import httpx
from gigachat import exceptions
# pylint: disable=no-name-in-module
from langchain.chat_models import GigaChat
from langchain.schema import HumanMessage, SystemMessage
from openai import OpenAI, OpenAIError

from . import classifier_promt, GIGA_CHAT_KEY, OPENAI_API_KEY, OPENAI_PROXY_URL

client = OpenAI(
    base_url=OPENAI_PROXY_URL,
    api_key=OPENAI_API_KEY,
    http_client=httpx.Client(verify=False)
    )
chat = GigaChat(credentials=GIGA_CHAT_KEY, verify_ssl_certs=False, model='GigaChat-Plus',
                temperature=0.05, scope="GIGACHAT_API_CORP")


def classify_merged(text):
    """функция для присваивания ярлыков, входящему сообщению

    Args:
        msg (str): сообщения пользователя

    Returns:
        lst: список ярлыков
    """
    try:
        completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": classifier_promt},
                    {"role": "user", "content": text}
                    ],
                temperature = 0.05
                )
        gpt_result = completion.choices[0].message.content
        if gpt_result.startswith('['):
            gpt_result = gpt_result[1:-1]
        gpt_result = gpt_result.split(', ')
        gpt_result = [i[1:-1] if i.startswith("'") or i.startswith("\"") else i for i in gpt_result]
    except OpenAIError:
        gpt_result = []
    try:
        messages = [SystemMessage(content=classifier_promt)]
        messages.append(HumanMessage(content=json.dumps(text, ensure_ascii=False)))
        giga_result = chat(messages).content
        if giga_result.startswith('['):
            giga_result = giga_result[1:-1]
        giga_result = giga_result.split(', ')
        giga_result = [i[1:-1] if i.startswith("'") or i.startswith("\"") else i for i in giga_result]
    except exceptions.ResponseError:
        giga_result = []

    if gpt_result == [] and giga_result == []:
        return {"error": "Произошла ошибка при обращении к API GigaChat и Chat GPT, повторите запрос"}
    merged_result = list(set(gpt_result + giga_result))

    return {"msg_classes": merged_result}
