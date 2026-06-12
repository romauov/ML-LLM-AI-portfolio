"""
Генерация текста рассылок

@author Dmitry Abramov
@author Koltashev Yaroslav
"""
import json
import logging

from flask import request

from .templates_methods.template import dummy_template_v2
from .templates_methods.saiga_api import saiga_promt_v2
from .templates_methods.yandex_api import yandex_gen_request
from . import blueprint


@blueprint.route('/gpt_templater_v2', methods=['POST'])
def generate_v2():
    """
    Api доступно по url: https://ai.m16.tech/api/gpt_templater_v2
    
    Принимает POST запрос
    Форма json:
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
    
    Возвращает: {
        "title": "Заголовок",
        "text": "Текст сгенерированного коммерческого предложения"
    }
    """
    logger = logging.getLogger("text_templater_routes_logger")
    if len(logger.handlers) == 0:
        file_handler = logging.FileHandler("log/text_templater_routes_logger.log", mode='a')
        formatter = logging.Formatter('[%(levelname)-10s] %(asctime)-25s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    request_data = request.get_json()
    logger.info(json.dumps(request_data, ensure_ascii=False))

    if request_data['model'].lower() == 'template':
        result = dummy_template_v2(request_data)
    elif request_data['model'].lower() == 'saiga':
        result = saiga_promt_v2(json.dumps(request_data))
    elif request_data['model'].lower() == 'yagpt':
        result = yandex_gen_request(json.dumps(request_data))
    else:
        result = {'error': 'Ошибка в названии модели, модель не найдена'}

    logger.info("model: %s | json: %s\n", request_data['model'], json.dumps(result, ensure_ascii=False))
    return json.dumps(result, ensure_ascii=False)
