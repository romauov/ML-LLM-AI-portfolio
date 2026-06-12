"""
функции для Chat GPT

@author Sergei Romanov
"""
import ast
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
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system", "content": f"""Тебе приходит запрос пользователя, в котором содержится наименование продукта,
             твоя задача - выделить из запроса продукт и отфильтровать список {products_list} по продукту из запроса,
             формат вывода - только список продуктов в формате python, без комментариев и дополнений"""
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
    return ast.literal_eval(list_str)


def get_prices(df, products, cols_to_drop=None):
    """Получение цен на определённые виды продукции по первому столбцу

    Args:
        df (pd.DataFrame): Исходный DataFrame с данными
        products (list): Список названий продуктов для фильтрации
        cols_to_drop (list, optional): Список столбцов для удаления. По умолчанию None.

    Returns:
        str: JSON с отфильтрованными данными
    """
    first_column_name = df.columns[0]

    df = df[df[first_column_name].isin(products)]

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
    return "сообщение менеджеру передано"


def generate_tools(tools_list):
    """json schema c описанием функций

    Args:
        tools_list (lst): список функций

    Returns:
        lst: json schema
    """
    tools_dict = {
        'get_prices': {
            "type": "function",
            "function": {
                "name": "get_prices",
                "description": "Получение цены на продукты. Функция принимает DataFrame с данными df=self.price_list",
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
        'get_full_pricelist': {
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
        'call_manager': {
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
    }
    tools = []
    for tool in tools_list:
        tools.append(tools_dict[tool])
    return tools
