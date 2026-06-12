"""
Сервис для квалификации входящих сообщений заданным набором ярлыков с помощью Chat GPT

example_input = 'добрый день можно получит прайс лист'

example_output = {"msg_classes": ['запрос прайса']}
    
@author Sergei Romanov
"""
import httpx
from openai import OpenAI, OpenAIError

from . import classifier_promt, OPENAI_API_KEY, OPENAI_PROXY_URL

client = OpenAI(
    base_url=OPENAI_PROXY_URL,
    api_key=OPENAI_API_KEY,
    http_client=httpx.Client(verify=False)
    )

def classify_gpt(text):
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
        result = completion.choices[0].message.content
        if result.startswith('['):
            result = result[1:-1]
        result = result.split(', ')
        result = [i[1:-1] if i.startswith("'") or i.startswith("\"") else i for i in result]

        return {"msg_classes": result}
    except OpenAIError as e:
        return {"error": f"Произошла ошибка при обращении к API Chat GPT: {e}, повторите запрос"}
    