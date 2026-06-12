"""
Генерация текста объявления

@author Marat Ibatullin
"""
import os

from gigachat import exceptions
# pylint: disable=no-name-in-module
from langchain.chat_models import GigaChat
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

giga_token = os.getenv('GIGA_TOKEN')

chat = GigaChat(credentials=giga_token,
                verify_ssl_certs=False,
                temperature=0.6,
                model = 'GigaChat-Pro',
                scope="GIGACHAT_API_CORP")

def giga_prompt_advertised(json_data):
    """
    Генерация текста объявления с помощью API Gigachat

    json_data: dict, следующего формата:
    {
   "deal_type": "buy",
   "title": "Test 4 ",
   "descr": "Индейка, крыло, локоть, 165 руб.",
   "category_id": "1",
   "type1": "Баранина",
   "type2": "12 разрубов",
   "state": "охл",
   "certification": "ГОСТ",
   "price": 500,
   "delivery_info": "Самовывоз",
   "unitCount": "9999",
   "unit": "кг",
   "user_company_id": 357126,
   "user_company_name": "Тестируем тестируем!",
   "company_descr": "Лучшая компания для тестирования!",
   "author_firstname": "Иван",
   "author_lastname": "Иванов",
   "author_position": "Менеджер",
   "addresses": "Россия, г Москва, ул Тестовская",
   "email": "randommail@mail.ru",
   "phones": "+71112223344",
   "model": "template",
   "temperature": 0.6
    }

    Возвращает json: {
        "title": "Заголовок",
        "text": "Текст сгенерированного объявления"
    }

    """
    template = """Шаблон объявления:
    <Описание компании>

    <Главная позиция>

    <Призыв> - Например "Звоните и мы все расскажем!"
    """
    example = """Пример, который ты можешь использовать, но тебе необязательно его придерживаться:
    Приморская рыбная компания - рады предложить Вам свежемороженую продукцию дикой рыбы, произведенную в Дальневосточном регионе.
    Дикая рыба – натуральный источник белка и полиненасыщенных жирных кислот Омега -3, укрепит иммунитет, защитит от негативных внешних факторов, снизит уровень холестерина, очистит сосуды, нормализует работы щитовидной железы и сердца.

    Мы реализуем:
    Плавник кальмара, Декабрь-январь 2024, Подход терминал Назимова 26.01

    Звоните и мы все расскажем!
    """
    messages = [
        SystemMessage(content="Ты маркетолог и пишешь маркетинговые предложения по продаже мясной"
                              " и рыбной продукции в сфере B2B рынка АПК"),
        HumanMessage(content=template),
        HumanMessage(content="Строго придерживайся этого шаблона."
                              " Не пиши в тексте названия из шаблона"),
        HumanMessage(content=example),
        HumanMessage(content="Тебе необязательно строго придерживаться примера,"
                             " но ты можешь перефразировать их, верни только "
                             "текст самого маркетингового предложения"),
        ]
    messages.append(HumanMessage(content=f"""Используй шаблон и пример текста объявления для написания текста и
                                 заголовок к тексту маркетингового предложения, выдели в заголовке название предлагаемой продукции и релевантность для пользователя,
                                 например Баранина 12 частей или Мясо говядины.
                                 Информация о компании {json_data['user_company_name']}: {json_data['company_descr']}
                                 Текст для объявления: по продаже {json_data['type1']} {json_data['type2']} {json_data['price']} рублей.
                                 """))
    # pylint: disable=broad-exception-caught
    # pylint: disable=bare-except
    try:
        text = chat(messages).content
    except exceptions.ResponseError:
        return {"error": "Ошибка в авторизации. Проверьте токен"}
    except Exception as exception:
        return {"error": f"Произошла ошибка при обращении к API GigaChat: {exception}"}

    try:
        title = text[:text.find('\n')]
        text = text[text.find('\n')+1:]
        if text.startswith("\n"):
            text = text.lstrip("\n")
    except:
        title = 'Заголовок не найден'

    return {'title': title, "text": text}
    