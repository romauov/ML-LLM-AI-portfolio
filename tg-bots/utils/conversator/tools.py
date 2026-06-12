"""
функции для Chat GPT

@author Sergei Romanov
"""
import ast
import datetime
import json
import re


async def pick_products(client, model, products_list, user_promt):
    """подбор продуктов под запрос пользователя

    Args:
        client (object): openai client
        model (str): название модели
        products_list (list): список доступных продуктов
        user_promt (str): запрос пользователя

    Returns:
        list: список подобранных продуктов
    """
    pick_promt = f"""
    Ты — эксперт по анализу пользовательских запросов и выбору продуктов. Твоя задача — принимать входящее сообщение от пользователя и выбирать из предоставленного списка продуктов те, которые максимально соответствуют запросу.
    products_list - {products_list}

    **Входные данные:**
    1.  `user_query`: Строка, содержащая запрос пользователя.


    **Задача:**
    Проанализируй `user_query` и выбери из `products_list` все продукты, которые подходят под запрос пользователя.

    **Формат вывода:**
    Выведи список подходящих продуктов строго в формате Python. Если подходящих продуктов нет, выведи пустой список.

    **Пример:**
    `user_query`: "Мне нужен смартфон с хорошей камерой"
    `products_list`: ["iPhone 13 Pro", "Samsung Galaxy S22 Ultra", "Ноутбук Dell XPS 15", "Наушники Sony WH-1000XM4", "Смартфон Xiaomi 12"]

    **Ожидаемый вывод:**
    ```python
    ["iPhone 13 Pro", "Samsung Galaxy S22 Ultra", "Смартфон Xiaomi 12"]
    ```
    """
    response = await client.chat.completions.create(
        model='google/gemini-2.5-flash-pre-05-20',
        messages=[
            {
                "role": "system", "content": pick_promt
            },
            {"role": "user", "content": user_promt}
        ],
        temperature=0.05,
        extra_headers={"X-title": "tg-bots"}
    )
    text = response.choices[0].message.content
    text = ' '.join(text.split())
    pattern = r'\[.*?\]'
    match = re.search(pattern, text)
    list_str = match.group(0)
    return ast.literal_eval(list_str), response.usage.prompt_tokens, response.usage.completion_tokens


def get_prices(df, products, product_col_name='вид продукции', cols_to_drop=None):
    """ получение цен на определённый вид продукции

    Args:
        product (str): название продукта
    Returns:
        str: json с данными о продукте
    """
    df = df[df[product_col_name].isin(products)]
    if cols_to_drop is not None:
        df = df.drop(columns=cols_to_drop)
    return json.dumps(df.to_dict(orient='records'), ensure_ascii=False)


def get_full_pricelist(df):
    """ получение прайс-листа по всей продукции

    Returns:
        str: json с данными о продуктах
    """
    return json.dumps(df.to_dict(orient='records'), ensure_ascii=False)


def call_manager(path, userpromt):
    """ вызов менеджера

    Args:
        userpromt (str): запрос пользователя

    Returns:
        str: подтверждение отправки запроса
    """
    # self.message_for_manager = userpromt
    with open(f'{path}/call_manager.txt', 'a', encoding='utf-8-sig') as f:
        newline = str(datetime.datetime.now()) + ' ' + userpromt + '\n'
        f.write(newline)
    return "сообщение менеджеру передано"


def generate_tools(
        func_description="Получение цены, срока поставки, условий оплаты, описания товара, фотографий и документов из прайс-листа для подходящих продуктов"):
    """json schema c описанием функций

    Args:
        products_list (lst): список продуктов

    Returns:
        lst: json schema
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_prices",
                "description": f"{func_description} \
                    Функция принимает DataFrame с данными df=self.price_list",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "df": {
                            "type": "object",
                            "description": "DataFrame с данными, необходимыми для получения информации о продуктах."
                        },
                        "products": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": f"Наименование продукции"
                            }
                        }
                    },
                    "required": ["df", "products"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_full_pricelist",
                "description": "Получение прайслиста по всей продукции. Функция принимает DataFrame с данными и всегда использует df=self.price_list.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "df": {
                            "type": "object",
                            "description": "DataFrame с данными, необходимыми для получения информации о продуктах. Всегда используется df=self.price_list."
                        }
                    },
                    "required": ["df"]
                }
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
                        "path": {
                            "type": "string",
                            "description": "путь к файлу для записи обращения"
                        },
                        "userpromt": {
                            "type": "string",
                            "description": "сообщение пользователя"
                        }
                    },
                    "required": ["path", "userpromt"]
                }
            }
        }
    ]
