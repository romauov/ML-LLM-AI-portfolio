# Генерация текста для рассылок

# Оглавление
## [Описание](#описание)
## [Api v1](#api-v1)
* [curl](#curl)
## [Api v2](#api-v2)
* [curl v2](#curl-v2)
## [Api для текста объявления](#api-для-текста-объявления)
* [сurl для генерации текста объявления](#curl-для-генерации-текста-объявления)
## [Демостраница](#демостраница)
## [Возвращаемые ошибки](#возвращаемые-ошибки)
* [Ошибка с ChatGPT](#ошибка-с-chatgpt)
* [Ошибки с GigaChat](#ошибки-с-gigachat)
* [Ошибка при выборе модели](#ошибка-при-выборе-модели)
## [Пример запроса через Postman](#пример-запроса-через-postman)
## [Пример ответа](#пример-ответа)

# Описание
Сервис генерации текста рассылок с помощью API openai.

Для генерации текстовых материалов используется унифицированный промт, который находится в templater.py

# Api v1
Первая версия Api доступно ссылке: (https://ai.m16.tech/api/gpt_templater)

```json
Принимает: 
{
   "deal_type": "buy",
   "title": "Test 4 ",
   "descr": "Большой опыт продаж, хоршие отзывы клиентов. Россия. Самовывоз",
   "category_id": "1",
   "category": "Вид мяса Баранина тушка охлаждённая",
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
   "price": "500.0",
   "model": "template",
   "temperature": 0.6
}
```

model:
* template - замена участков в шаблоне
* gpt - использование API OpenAI
* gigachat - использование API GigaChat

Возвращает: json({"title": "Заголовок", "text": "текст рассылки"})

# Curl
```sh
curl -u "{{API_USER}}:{{API_PASSWORD}}" -d '{"deal_type": "buy",  "title": "Test 4 ", "descr": "Большой опыт продаж, хоршие отзывы клиентов. Россия. Самовывоз", "category_id": "1", "category": "Вид мяса Баранина тушка охлаждённая", "unitCount": "9999", "unit": "кг", "user_company_id": 357126, "user_company_name": "Тестируем тестируем!", "author_firstname": "Иван", "author_lastname": "Иванов", "author_position": "test_position", "addresses": "Россия, г Москва, ул Тестовская", "email": "randommail@mail.ru", "phones": "+71112223344", "price": "500.0", "model": "template", "temperature": 0.6}' -H "Content-Type: application/json" -X POST https://ai.m16.tech/api/gpt_templater
```

# Api v2
Вторая версия Api доступно ссылке: (https://ai.m16.tech/api/gpt_templater_v2)

```json
Принимает: 
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
        "advantages": "• Льготная доставка\n• Скидки при больших партиях",
        "author_firstname": "Иван",
        "author_lastname": "Иванов",
        "author_position": "Менеджер",
        "addresses": "Россия, г Москва, ул Тестовская",
        "email": "randommail@mail.ru",
        "phones": "+71112223344",
        "other_prod": "• Печень говяжья - 380 руб/кг\n• СубПродукты - 240 руб/кг",
        "model": "template",
        "temperature": 0.6
    }
```

model:
* template - замена участков в шаблоне
* gpt - использование API OpenAI
* gigachat - использование API GigaChat
* saiga - использование fine-tuned saiga через API

Возвращает: json({"title": "Заголовок", "text": "текст рассылки"})


# Curl v2
```sh
curl --location 'https://ai.m16.tech/api/gpt_templater_v2' --header 'Content-Type: application/json' --header 'Authorization: Basic {{BASE64_AUTH}}' --data-raw '{"deal_type": "buy","title": "Test 4 ","descr": "Индейка, крыло, локоть, 165 руб.","category_id": "1","type1": "Баранина","type2": "12 разрубов","state": "охл","certification": "ГОСТ","price": 500,"delivery_info": "Самовывоз","unitCount": "9999","unit": "кг","user_company_id": 357126,"user_company_name": "Тестируем тестируем!","company_descr": "Лучшая компания для тестирования!","advantages": "• Льготная доставка\n• Скидки при больших партиях","author_firstname": "Иван","author_lastname": "Иванов","author_position": "Менеджер","addresses": "Россия, г Москва, ул Тестовская","email": "randommail@mail.ru","phones": "+71112223344","other_prod": "• Печень говяжья - 380 руб/кг\n• СубПродукты - 240 руб/кг","model": "gigachat_maridze","temperature": 0.6}'
```

# Api для текста объявления
Api доступно ссылке: (https://ai.m16.tech/api/gpt_adv_templater)

```json
Принимает: 
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
        "advantages": "• Льготная доставка\n• Скидки при больших партиях",
        "author_firstname": "Иван",
        "author_lastname": "Иванов",
        "author_position": "Менеджер",
        "addresses": "Россия, г Москва, ул Тестовская",
        "email": "randommail@mail.ru",
        "phones": "+71112223344",
        "other_prod": "• Печень говяжья - 380 руб/кг\n• СубПродукты - 240 руб/кг",
        "model": "template",
        "temperature": 0.6
    }
```

model:
* gigachat - использование API GigaChat

Возвращает: json({"title": "Заголовок", "text": "текст объявления"})

# Curl для генерации текста объявления
```sh
curl --location 'https://ai.m16.tech/api/gpt_adv_templater' --header 'Content-Type: application/json' --header 'Authorization: Basic {{BASE64_AUTH}}' --data-raw '{"deal_type": "buy","title": "Test 4 ","descr": "Индейка, крыло, локоть, 165 руб.","category_id": "1","type1": "Баранина","type2": "12 разрубов","state": "охл","certification": "ГОСТ","price": 500,"delivery_info": "Самовывоз","unitCount": "9999","unit": "кг","user_company_id": 357126,"user_company_name": "Тестируем тестируем!","company_descr": "Лучшая компания для тестирования!","advantages": "• Льготная доставка\n• Скидки при больших партиях","author_firstname": "Иван","author_lastname": "Иванов","author_position": "Менеджер","addresses": "Россия, г Москва, ул Тестовская","email": "randommail@mail.ru","phones": "+71112223344","other_prod": "• Печень говяжья - 380 руб/кг\n• СубПродукты - 240 руб/кг","model": "gigachat","temperature": 0.6}'
```

# Демостраница

Демостраница для генерации КП и текста объявления доступна по ссылке: https://ai.m16.tech/gradio/text_generation
Демостраница для генерации КП и текста второй версии объявления доступна по ссылке: https://ai.m16.tech/gradio/text_generation_v2
Для выбора типа текста необходимо выбрать radiobutton вначале страницы

# Описание полей демостраницы

| Поле              | Обозначение                                                                                          |  Примечение                                       |
|-------------------|------------------------------------------------------------------------------------------------------|---------------------------------------------------|
| deal_type         | Тип объявления buy (покупка) или продажа (sale)                                                      | Можно не указывать для saiga, gigachat            |
| title             | Заголовок объявления, написанный пользователем                                                       | Можно не указывать                                |
| descr             | Короткое описание объявления                                                                         | Нужно указать                                     |
| category_id       | id категории                                                                                         | Можно не указывать                                |
| type1             | Верхнеуровневая категория продукции                                                                  | Необходимо указать                                |
| type2             | Низкоуровневая категория продукции                                                                   | Необходимо указать                                |
| state             | Состояние продукции                                                                                  | Можно не указать                                |
| certification     | Сертификация продукции                                                                               | Можно не указать                                |
| unitCount         | количество единиц                                                                                    | Можно не указывать                                |
| unit              | кг, тонны, единицы измерения                                                                         | Можно не указывать                                |
| user_company_id   | id компании                                                                                          | Можно не указывать                                |
| user_company_name | название компании                                                                                    | Необходимо указать                                |
| company_descr     | Информация о компании                                                                                | Необходимо указать                                |
| author_firstname  | Имя менеджера от лица, которого делается рассылка                                                    | Необходимо указать                                |
| author_lastname   | Фамилия менеджера от лица, которого делается рассылка                                                | Необходимо указать                                |
| author_position   | Занимаемая должность                                                                                 | Необходимо указать                                |
| addresses         | Адрес склада / офиса                                                                                 | Можно не указывать                                |
| email             | электронная почта                                                                                    | Необходимо указать                                |
| phones            | номер телефона для связи                                                                             | Необходимо указать                                |
| price             | цена                                                                                                 | Необходимо указать                                |
| delivery_info     | информация по доставке                                                                               | Можно не указать                                |
| advantages        | Преимущества компании                                                                                | Можно не указать                                |
| other_prod        | Продукция, которой еще торгует компания                                                              | Можно не указать                                |
| temperature       | Насколько генерация будет "хаотичной", чем выше значение - тем больше разницы при между генерациями,  высокое значение может привести к ухудшению | Значение по умолчанию 0.5                         |

# Возвращаемые ошибки
## Ошибка с ChatGPT
С 17 ноября 2023 года OpenAI ограничил доступ к API из ряда стран, из-за чего API не работает из России

Возвращаемая ошибка:
```json
{  
   "error": "Произошла ошибка при обращении к OpenAI"
}
```
## Ошибки с GigaChat
Ошибка с неправильным токеном доступа:
```json
{
   "error": "Ошибка в авторизации. Проверьте токен"
}
```

Ошибка при обращении к GigaChat
```json
{
   "error": "Произошла ошибка при обращении к API GigaChat: (URL('https://gigachat.devices.sberbank.ru/api/v1/chat/completions'), 401, b'{\"status\":401,\"message\":\"Unauthorized\"}\\n', Headers([('server', 'nginx'), ('date', 'Wed, 06 Dec 2023 11:17:50GMT'), ('content-type','application/json; charset=utf-8'), ('content-length', '40'), ('connection', 'keep-alive'), ('x-request-id', 'b1e54164-146b-4d79-9158-cca0d67d1177'), ('x-session-id', '704bd5b2-1349-4918-85b7-f179d86cbf48'), ('allow', 'GET, POST'), ('strict-transport-security', 'max-age=31536000; includeSubDomains'), ('allow', 'GET, POST'), ('strict-transport-security', 'max-age=31536000; includeSubDomains')]))"
}
```

## Ошибка при выборе модели
API принимает на данный момент следующие варианты моделей:
* gpt - использование API ChatGPT
* template - использование шаблона
* gigachat - использование API GigaChat
* gigachat_maridze - использование API GigaChat c обновленным промтом
* saiga - использование API развернутой на 3090 дообученной saiga

## Пример запроса через Postman
![Alt text](image.png)

<hr>

## Пример ответа

![Alt text](image-3.png)