"""
Генерация текста рассылок через YaGPT

@author Marat Ibatullin
"""

import json
import requests

from yandex_chain import YandexLLM


def yandex_gen_request(json_data):
    """
      Генерация текста с помощью API YaGPT

      1. Получение iamToken
      2. Создание промта
      3. Отправка запроса
      4. Парсинг ответа

      json_data: dict, следующего формата:
      {
          "deal_type": "buy",
          "title": "Test 4 ",
          "descr": "Большой опыт продаж, хоршие отзывы клиентов. Россия. Самовывоз",
          "category_id": "1",
          "category": "Вид мяса Баранина Разруб 12 частей",
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
          "price": "500.0"
      }
      """
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    data = {"yandexPassportOauthToken":
            "y0_AgAAAABjTa4DAATuwQAAAAEOYs3uAACjalDsb4RI8KkQo-kQo_YgCkw0UA"}

    try:
        response = requests.post(url,
                                 json=data,
                                 timeout=30)
        response.raise_for_status()
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            return {'error': f"Ошибка при декодировании JSON ответа: {e}"}
        try:
            iam_token = response_data['iamToken']
        except KeyError:
            return {'error': "Ошибка: ключ 'iamToken' не найден в JSON ответе"}
        if iam_token:
            text = ya_prompt(json_data, iam_token)
            if text.startswith("Ошибка"):
                return {'error': "Ошибка обращения к сервиcу YaGPT"}
            try:
                title = text[:text.find('\n')]
                text = text[text.find('\n')+1:]
                if text.startswith("\n"):
                    text = text.lstrip("\n")
            except:  # pylint: disable=bare-except
                title = 'Заголовок не найден'
            return {'title': title.replace('Заголовок: ', ''), "text": text.strip()}
        return {'error': "Ошибка: iamToken не найден в ответе"}
    except requests.exceptions.RequestException as e:
        return {'error': f"Ошибка при выполнении запроса: {e}"}


def ya_prompt(json_data, iam_token):
    """
      Подготовка промта и обращение е сервису
    """

    llm = YandexLLM(folder_id="b1gd1t3qqo1ti4v6bc1q",
                    iam_token=iam_token,
                    use_lite=False,
                    temperature=0)

    # template = """Шаблон маркетингового предложения:
    # <Приветствие> - доброе утро, добрый день

    # <Информация о компании>

    # <Название компании> предлагает ознакомиться с продукцией:
    # <Список продукции> (Используй нумерацию)

    # <адрес склада>

    # <Название компании>
    # <Телефон>
    # <Адрес электронной почты>
    # <сайт>.
    # """
    # example = """Пример, который ты можешь использовать, но тебе необязательно его придерживаться:
    # Доброе утро!

    # Миссия компании “Гурьянов и партнеры” - продавать качественную импортную рыбу по выгодной для клиента цене.

    # Компания "Гурьянов и партнеры" предлагает ознакомиться с интересными позициями из нашего ассортимента:
    #     • Горбуша НР/ПСГ (Всеволод Сибирцев Камчатка) — 205 руб. с НДС
    #     • Горбуша ПБГ (ИП Аскеров, Камчатка) — 250 руб. с НДС
    #     • Горбуша ПБГ (Пеликан, Сахалин) 330 руб. с НДС

    # Поставки рыбы напрямую от поставщиков, гарантия качества.
    # Адрес склада: Москва, ул. Ветеранов

    # С уважением, Артем Линейцев
    # ООО «Гурьянов и партнеры»
    # Телефоны:
    # +7 (812) 920-64-13
    # +7 (910) 109-35-71
    # 8 800 250-78-05
    # E-mail: gurj-yanov@fishr.ru
    # Сайт: kilkann.ru
    # """
    json_data = json.loads(json_data)
    content = f"""Используй шаблон и пример маркетингового предложения для написания текста и
                                 заголовок к тексту маркетингового предложения, выдели в заголовке название предлагаемой продукции и релевантность для пользователя,
                                 например Баранина 12 частей или Мясо говядины.
                                 Текст для маркетингового предложения: по продаже {json_data['type1']} {json_data['type2']} {json_data['price']} рублей,
                                 от компании {json_data['user_company_name']}, Информация о компании {json_data['company_descr']}.
                                 Адрес склада: {json_data['addresses']}.
                                 Доставка от {json_data['unitCount']} {json_data['unit']}.
                                 Контакты:
                                 Номер телефона: {json_data['phones']},
                                 Адрес электронной почты: {json_data['email']}
                                 Менеджер: {json_data['author_firstname']} {json_data['author_lastname']}.
                                 """
    # pylint: disable=broad-exception-caught
    try:
        text = llm.invoke(content)
        return text
    except Exception as e:
        error_text = f"Ошибка: {e}"
        return error_text
