"""
Шаблон результата для модели генерации текста

@author Dmitry Abramov
"""
import numpy as np


def dummy_template_v2(json_data):
    """
    Генерация текста с помощью шаблона

    json_data: dict, следующего формата:
    {
        "deal_type": "buy",
        "title": "Test 4 ",
        "descr": "Индейка, крыло, локоть, 165 руб.",
        "category_id": "1",
        "type1": "Баранина", NEW
        "type2": "12 разрубов", NEW
        "state": "охл", NEW
        "certification": "ГОСТ", NEW
        "price": 500,
        "delivery_info": "Самовывоз", NEW
        "unitCount": "9999",
        "unit": "кг",
        "user_company_id": 357126,
        "user_company_name": "Тестируем тестируем!",
        "company_descr": "Лучшая компания для тестирования!",
        "author_firstname": "Иван",
        "author_lastname": "Иванов",
        "author_position": "test_position",
        "addresses": "Россия, г Москва, ул Тестовская",
        "email": "randommail@mail.ru",
        "phones": "+71112223344",
        "model": "template",
        "temperature": 0.6
    }
    """
    greetings = np.random.choice(['Здравствуйте', 'Доброе утро', 'Добрый день'])

    product = ' '.join([json_data['type1'], json_data['type2']])

    if json_data['deal_type'] == 'sale':
        title = f"{product} от производителя!"

        text = f"""
        {greetings}

        Компания {json_data['user_company_name']} предлагает ознакомиться с следующими позициями:
        - {product} - {json_data['price']}
        Поставки {product} напрямую от поставщиков, гарантия качества.
        Также все цены можно получить по электронной почте
        {json_data['descr']}

        С уважением {json_data['author_lastname']} {json_data['author_firstname']}, {json_data['phones']}, {json_data['email']}
        """
    else:
        title = f"Куплю {product}"

        text = f"""
        {greetings}

        Компания {json_data['user_company_name']} интересуется следующей продукцией:
        - {product} - {json_data['price']}
        {json_data['descr']}

        С уважением {json_data['author_lastname']} {json_data['author_firstname']}, {json_data['phones']}, {json_data['email']}
        """

    return {'title': title, "text": text}
