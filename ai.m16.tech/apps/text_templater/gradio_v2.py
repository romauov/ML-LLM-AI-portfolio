"""
Демостраница генерации маркетинговых предложений

@author Dmitry Abramov
"""
import gradio as gr
import pandas as pd
import requests


example = [[[
           ['deal_type', 'buy'],
           ['title', 'Test 4'],
           ['descr', 'Большой опыт продаж, хорошие отзывы клиентов. Россия. Самовывоз'],
           ['category_id', '1'],
           ['type1', 'Баранина'],
           ['type2', '12 разрубов'],
           ['state', 'охл'],
           ['certification', 'ГОСТ'],
           ['delivery_info', 'Самовывоз'],
           ['unitCount', '9999'],
           ['unit', 'кг'],
           ['user_company_id', 357126],
           ['user_company_name', 'Тестируем тестируем!'],
           ['company_descr', 'Лучшая компания для тестирования!'],
           ['author_firstname', 'Иван'],
           ['author_lastname', 'Иванов'],
           ['author_position', 'test_position'],
           ['addresses', 'Россия, г Москва, ул Тестовская'],
           ['email', 'randommail@mail.ru'],
           ['phones', '+71112223344'],
           ['price', '500.0'],
           ['temperature', 0.2]
          ], ]]

df_schema = [['deal_type', ''],
             ['title', ''],
             ['descr', ''],
             ['category_id', ''],
             ['type1', ''],
             ['type2', ''],
             ['state', ''],
             ['certification', ''],
             ['delivery_info', ''],
             ['unitCount', ''],
             ['unit', ''],
             ['user_company_id', ''],
             ['user_company_name', ''],
             ['company_descr', ''],
             ['author_firstname', ''],
             ['author_lastname', ''],
             ['author_position', ''],
             ['addresses', ''],
             ['email', ''],
             ['phones', ''],
             ['price', ''],
             ['temperature', 0.5]
            ]


def text_generation_v2(data, model):
    """
    Парсинг полученного датафрейма c демостраницы в dict(json)

    arguments:
    data: gr.Dataframe -- Датафрейм с данными, которые вводит пользователь
    type_of_text: str -- Тип текста (объявление/рассылка)
    model: str -- Модель Тип (saiga, yagpt, template)
    """
    # Преобразование датафрейма в json

    data = pd.DataFrame(data)
    data = dict(zip(list(data['col'].values), list(data['value'].values)))

    data['model'] = model
    data['temperature'] = float(data['temperature'])


    url = 'https://ai.m16.tech/api/gpt_templater_v2'

    result = requests.post(url,
                           json=data,
                           auth=requests.auth.HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                           timeout=180)
    result = list(result.json().values())
    print(result)
    return result


def gr_generation_interface_v2():
    """
    Интерфейс для веб сервиса генерации текста
    """
    return gr.Interface(
        fn=text_generation_v2,
        inputs=[
                gr.Dataframe(headers=["col", "value"],
                             value=df_schema,
                             label="Входные данные",
                             wrap=True),
                gr.Radio(['saiga', 'yagpt', 'template'],
                         value='gigachat', label="Модель", info="Модель для генерации текста"),
                ],
        examples=example,
    outputs=[gr.Textbox(label='Заголовок'),
             gr.Textbox(label='Текст КП')]
)
