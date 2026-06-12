"""
Демостраница работы лидогенератора на основе карточек

@author Marat Ibatullin
"""
import requests
from requests.auth import HTTPBasicAuth

import gradio as gr
import pandas as pd


def recommender(tsop_id, number_of_users, site, info, prods, position):#pylint: disable=too-many-arguments
    """
    Рекомендации на основе портрета и экспорт df в csv для загрузки со страницы

    arguments:
    tsop_id: int -- id юзера в ЦОПе
    number_of_users: int -- Число пользователей на рассылку
    site: str -- Сайт, для которого составляется поиск(meatinfo/fishretail)
    info: str -- Информация о компании
    prods: str -- Строка в которой написаны продукты
    position: str -- Должность пользователя для портрета
    """
    information_json={}
    information_json['Любимые продукты'] = prods
    information_json['Краткое описание компании'] = info
    information_json['Должность'] = position
    str(information_json)
    result = requests.post('https://ai.m16.tech/api/card_recommendations',
                        json={"tsop_id": tsop_id,
                              "site": site,
                              "number_of_users": number_of_users,
                              "user_portrait": str(information_json)},
                        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                        timeout=150
                        )
    result = list(result.json().values())
    result_100 = pd.DataFrame({'email': result[0]})
    result_10 = pd.DataFrame({'email': result[0][:10]})
    result_100.to_csv("output.csv", index=False)

    return result_10, gr.File.update(value="output.csv", visible=True)


def gr_recommendation_card_interface():
    """
    Фронт для страницы
    """
    interface =  gr.Interface(fn = recommender, inputs=[
                gr.Number(label="ЦОП id", info="id клиента, от лица которого отправляется предложение", precision=0),
                gr.Slider(10, 200, value=100, label="Число пользователей", info="Выберете между 10 и 200"),
                gr.Radio(['meatinfo', 'fishretail'],
                         value='meatinfo', label="site", info="Сайт для построения рекомендаций"),
                gr.Textbox(label="Информация о компании", info="Напишите информацию о компании"),
                gr.Textbox(label="Любимые продукты", info="Напишите любимые продукты"),
                gr.Textbox(label="Позиция", info="Напишите должность"),
                ],
            outputs=['dataframe', 'file'],
            examples=[
                [57,100, "fishretail", '''Компания занимается переработкой рыбы, переработчик. Занимается
                 оптовой торговлей продуктов своей переработки (филе, стейки, копчености и тд).''',
                "форель охлажденая",
                "менеджер по закупкам, руководитель отдела закупок"],
                ],
                allow_flagging="never",
    )

    return interface
