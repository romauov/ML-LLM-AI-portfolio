"""
Демостраница работы лидогенератора на основе Bert

@author Marat Ibatullin
"""
import requests
from requests.auth import HTTPBasicAuth

import gradio as gr
import pandas as pd


def recommender(tsop_id, number_of_users, site, context, search):
    """
    Рекомендации на основе текста объявления и экспорт df в csv для загрузки со страницы
    """
    result = requests.post('https://ai.m16.tech/api/bert_recommendations',
                        json={"tsop_id": tsop_id,
                              "site": site,
                              "number_of_users": number_of_users,
                              "context": context,
                              "search": search},
                        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                        timeout=30
                        )
    result = list(result.json().values())
    result_100 = pd.DataFrame({'email': result[0]})
    result_10 = pd.DataFrame({'email': result[0][:10]})
    result_100.to_csv("output.csv", index=False)

    return result_10, gr.File.update(value="output.csv", visible=True)


def gr_recommendation_bert_interface():
    """
    Фронт для страницы
    """
    interface =  gr.Interface(fn = recommender, inputs=[
                gr.Textbox(label="ЦОП id", info="id клиента, от лица которого отправляется предложение"),
                gr.Slider(10, 200, value=100, label="Число пользователей", info="Выберете между 10 и 200"),
                gr.Radio(["meatinfo", "fishretail"], value = 'meatinfo', label="Сайт", info="Сайт для продвижения"),
                gr.Textbox(label="Текст объявления", info="Напишите текст для поиска похожих объявлений"),
                gr.Textbox(label="Поисковый запрос", info="Напишите тип продукции для поиска похожих продуктов"),
                ],
            outputs=['dataframe', 'file'],
            examples=[
                [6,100, "meatinfo", "Продам: мясо говядины в отрубах б/к Говядина лопаточный отруб зам. 450 руб",
                "Говядина лопаточный отруб"],
                ],
                allow_flagging="never",
    )

    return interface
