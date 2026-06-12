"""
Интерфейс рекомендатора на основе ближайшего соседа

@author Dmitry Abramov
"""
import gradio as gr
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth


def export_csv(df):
    """
    Экспорт датафрейма в csv для загрузки со страница Gradio
    """
    df.to_csv("output.csv")
    return gr.File.update(value="output.csv", visible=True)

def recommender(product, number_of_users, tsop_id):
    """
    :params:
        product: str - продукт
        number_of_users
    :return:
        list - класс 
    """
    result = requests.post('https://ai.m16.tech/api/knn_recommenations',
                        json={"product": product,
                              "number_of_users": number_of_users,
                              "tsop_id": tsop_id},
                        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                        timeout=10)
    result = list(result.json().values())
    return pd.DataFrame({'email': result[0],
                         'userId': result[1]})

def gr_recommendation_interface():
    """
    Валидатора ответов 
    """
    with gr.Blocks() as interface:
        with gr.Column():
            button = gr.Button("Export")
            csv = gr.File(interactive=False, visible=False)

        with gr.Row():
            product = gr.Textbox(value='говядина мясо',
                                label='продукт',
                                placeholder="продукт")
            number = gr.Number(value=200, precision=0,
                            label="число пользователей")
            tsop_id = gr.Number(value=10, precision=0,
                            label="id клиента цопа")
            dataframe = gr.Dataframe(headers=["email", "userId"],
                                    datatype=["str", "number"])
            site = gr.Textbox(value='meatinfo',
                              label='site',
                              placeholder="site")
        button.click(export_csv, dataframe, csv)

        with gr.Column():
            recommendation = gr.Button("Найти пользователей")
            result = dataframe
            recommendation.click(recommender, [product, number, tsop_id, site], result)

    return interface
