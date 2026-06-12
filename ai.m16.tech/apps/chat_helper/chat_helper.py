"""
Сервис автоматического ответа на вопросы пользователя в соответствии с заданным регламентом и имеющимся прайслистом

example_input = 'нужны цены на вырезку'

example_output = {"reply": 
"Говяжья вырезка - 18 рублей за 1 кг, срок поставки 3 недели, халяльный продукт.
\nТелячья вырезка - 912 рублей за 1 кг, срок поставки 4 недели, не является халяльным продуктом.
\nЕсли вас заинтересовал какой-то конкретный вид, я могу дать более подробную информацию.", 
"charge": "2696 tokens, $0.002827"}
    
@author Sergei Romanov
"""
from __future__ import absolute_import
import datetime
import json
import httpx
import pandas as pd
import requests
from openai import OpenAI
# from openai import AsyncOpenAI

from chat_helper import OPENAI_API_KEY, PRICE_ID, REGLAMENT_ID, OPENAI_PROXY_URL

client = OpenAI(
# client = AsyncOpenAI(
    base_url=OPENAI_PROXY_URL,
    api_key=OPENAI_API_KEY,
    http_client=httpx.AsyncClient(verify=False)
    )
"""id google таблицы с прайс-листом"""
PRICE_LIST_URL = f'https://docs.google.com/spreadsheets/d/{PRICE_ID}/export?gid=0&format=csv'
"""id google документа с регламентом"""
REGLAMENT_URL = f'https://docs.google.com/document/d/{REGLAMENT_ID}/export?format=txt'

price_list = pd.read_csv(PRICE_LIST_URL)

my_file = requests.get(REGLAMENT_URL, timeout=30)
with open('apps/file_hosting/chat_helper/reglament.txt', 'wb') as some_file:
    some_file.write(my_file.content)
with open('apps/file_hosting/chat_helper/reglament.txt', encoding='utf-8-sig') as some_file:
    reglament = some_file.readlines()
# pylint: disable=invalid-name
reglament = ''.join(reglament)

"""тариф модели gpt-3.5-turbo"""
INPUT_RATE = 0.0010 / 1000
OUTPUT_RATE = 0.0020 / 1000

def get_chat_response_charge(input_tokens, output_tokens):
    """
    расчёт стоимости генерации оттвета в соответствии с заданным тарифом
    """
    return input_tokens * INPUT_RATE + output_tokens * OUTPUT_RATE

def get_prices(product):
    """
    Получение информации по продукту
    """
    return json.dumps(price_list[price_list['вид продукции'] == product].to_dict(orient='records'), ensure_ascii=False)
# pylint: disable=unused-argument
def get_full_pricelist():
    """
    Получение информации по всей продукции
    """
    return json.dumps(price_list[
        ['вид продукции', 'цена за 1 кг, рубли РФ']
        ].to_dict(orient='records'), ensure_ascii=False)

def call_manager(userpromt):
    """
    обращение к менеджеру
    """
    with open('log/chat_helper_call_manager.txt', 'a', encoding='utf-8-sig') as f:
        newline = str(datetime.datetime.now()) + ' ' + userpromt + '\n'
        f.write(newline)
    return "сообщение менеджеру передано"

def get_history(from_id, n_messages=10):
    """возвращает последние n сообщений из диалога с пользователем

    Args:
        from_id (int): id полььзоваеля в телеграме
        n_messages (int, optional): число сообщений для загрузки из истории. Defaults to 4.

    Returns:
        lst: список сообщений
    """
    try:
        with open(f'apps/file_hosting/chat_helper/{from_id}.json', 'r', encoding='utf-8-sig') as file:
            json_data = json.load(file)
            user_records = []
            for record in reversed(json_data):
                if record['role'] == 'user' or record['role'] == 'system':
                    user_records.append(record)
                if len(user_records) == n_messages:
                    break

    except FileNotFoundError:
        user_records = []

    return user_records[::-1]

def write_history(from_id, data):
    """запись истории диалога с пользователем

    Args:
        from_id (int): id пользователя в телеграме
        data (json): сообщение в формате chat gpt, json объект вида {"role": "user", "content": "user_promt"}
    """
    if from_id is None:
        return
    try:
        with open(f'apps/file_hosting/chat_helper/{from_id}.json', 'r', encoding='utf-8-sig') as file:
            json_data = json.load(file)
    except FileNotFoundError:
        json_data = []

    json_data.append(data)

    with open(f'apps/file_hosting/chat_helper/{from_id}.json', 'w', encoding='utf-8-sig') as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)
    return

def clear_history_for_chat(from_id):
    """очистка истории сообщений

    Args:
        from_id (int): id пользователя в телеграме
    """
    try:
        with open(f'apps/file_hosting/chat_helper/{from_id}.json', 'r', encoding='utf-8-sig') as file:
            json_data = []
        with open(f'apps/file_hosting/chat_helper/{from_id}.json', 'w', encoding='utf-8-sig') as file:
            json.dump(json_data, file, indent=4, ensure_ascii=False)
            return
    except FileNotFoundError:
        return

def run_conversation(user_promt, table_id=None, text_id=None, from_id=None):
    """Генерация реакции на пользовательское сообщение.
    Помимо дефолных регламента и прайс-листа, в аргументы можно передавать id гугл-документов с другими промтами.
    Args:
        user_promt (str): сообщение пользователя
        table_id (str, optional): id гугл-документа с прайс-листом. Defaults to None.
        text_id (str, optional): id гугл-документа с прайс-листом. Defaults to None.

    Returns:
        str: Сгенерированная реакция
    """
    if table_id:
        # pylint: disable=global-statement
        global price_list
        # pylint: disable=invalid-name
        new_price_list = f'https://docs.google.com/spreadsheets/d/{table_id}/export?gid=0&format=csv'
        price_list = pd.read_csv(new_price_list)

    if text_id:
        # pylint: disable=invalid-name
        new_reglament = f'https://docs.google.com/document/d/{text_id}/export?format=txt'
        # pylint: disable=global-statement
        # pylint: disable=redefined-outer-name
        global reglament
        my_file = requests.get(new_reglament, timeout=30)
        with open('apps/file_hosting/chat_helper/reglament.txt', 'wb') as some_file:
            some_file.write(my_file.content)
        with open('apps/file_hosting/chat_helper/reglament.txt', encoding='utf-8-sig') as some_file:
            reglament = some_file.readlines()
        reglament = ''.join(reglament)

    products_list = price_list['вид продукции'].unique().tolist()
    halal_products = price_list[price_list['халяльный продукт'] == 'да']['вид продукции'].unique().tolist()

    if from_id:
        messages=[
        {"role": "system", "content": reglament + \
         f'список продуктов в прайс-листе: {products_list}' + \
        f'список халяльных продуктов: {halal_products}'}]
        for msg in get_history(from_id):
            messages.append(msg)
        messages.append({"role": "user", "content": user_promt})
        write_history(from_id, {"role": "user", "content": user_promt})
    else:
        messages=[
        {"role": "system", "content": reglament + \
         f'список продуктов в прайс-листе: {products_list}' + \
        f'список халяльных продуктов: {halal_products}'},
        {"role": "user", "content": user_promt}
        ]
    tools = [{
        "type": "function",
        "function": {
            "name": "get_prices",
            "description": f"Получение цены, срока поставки, условий оплаты, описания товара, \
                фотографий и документов из прайс-листа для подходящих продуктов из списка {products_list}",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "Наименование продукции, например говяжья печень"
                        },
                    },
                "required": ["product"],
                }
            }
        },
        {"type": "function",
            "function": {
                "name": "get_full_pricelist",
                "description": "Получение прайслиста по всей продукции",
                }
            },
        {
            "type": "function",
            "function": {
                "name": "call_manager",
                "description": "Обращение к менеджеру",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "userpromt": {
                            "type": "string",
                            "description": "сообщение пользователя"
                        },
                    #"unit": {"type": "string", "enum": ["рубли РФ", "доллары США"]},
                    },
                    "required": ["userpromt"],
                }
            }
        }
            ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        )
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "get_prices": get_prices,
            "get_full_pricelist": get_full_pricelist,
            "call_manager": call_manager
            }
        messages.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)
            func_message = {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
                }
            messages.append(func_message)
            write_history(from_id, func_message)
    response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages
            )
    resp_text = response.choices[0].message.content
    write_history(from_id, {"role": "system", "content": resp_text})
    resp_charge = get_chat_response_charge(response.usage.prompt_tokens, response.usage.completion_tokens)
    resp_charge = str(response.usage.total_tokens) + ' tokens, $' + str(resp_charge)
    return json.dumps({"reply": resp_text, "charge": resp_charge, "from_id": from_id}, ensure_ascii=False)
