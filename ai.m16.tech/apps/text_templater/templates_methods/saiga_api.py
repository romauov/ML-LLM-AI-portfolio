"""
Генерация текста рассылок через saiga

@author Marat Ibatullin
"""
import requests


def saiga_promt_v2(json_data):
    """
    Генерация текста с помощью модели Saiga

    Сервис обращается к модели развернутой на 3090

    Для правок промта, обновления модели нужно подключиться к компьютеру, на котором развернута модель

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
    url = "{{INTERNAL_HOST}}:8080/saiga_mistral_templater/"
    response = requests.post(url, json_data, timeout=100)
    if response.status_code == 200:
        return response.json()
    return response.status_code
