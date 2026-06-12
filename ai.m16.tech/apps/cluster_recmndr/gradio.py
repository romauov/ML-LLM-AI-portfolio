"""
Демостраница работы лидогенератора на основе кластерного деления

@author Sergei Romanov
"""
import requests
from requests.auth import HTTPBasicAuth

import gradio as gr
import pandas as pd

def export_csv(df):
    """
    Экспорт датафрейма в csv для загрузки со страница Gradio
    """
    df.to_csv("output.csv")
    return gr.File.update(value="output.csv", visible=True)

def recommender(type1, type2, category_name=None, number_of_users=100):
    """
    Рекомендации на основе текста объявления и экспорт df в csv для загрузки со страницы
    """
    result = requests.post('https://ai.m16.tech/api/cluster_recmndr',
                        json={"type1": type1,
                              "type2": type2,
                              "category_name": category_name,
                              "number_of_users": number_of_users
                              },
                        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                        timeout=30
                        )
    result = list(result.json().values())
    return pd.DataFrame({'user_ids': result[0],
                         'emails': result[1]})

def gradio_cluster_recommender_interface():
    """
	Интерфейс градио
	"""
    with gr.Blocks() as interface:
        with gr.Column():
            button = gr.Button("Export")
            csv = gr.File(interactive=False, visible=False)

        with gr.Row():
            type1 = gr.Textbox(value='форель',
                               label='type1',
                               #placeholder="форель"
                               )
            type2 = gr.Textbox(value='разделка',
                               label='type2',
                               #placeholder="разделка"
                               )
            category_name = gr.Textbox(value=None,
                                       label='category_name',
                                       #placeholder="форель"
                                       )
            number_of_users = gr.Textbox(value=100,
                                 label='number_of_users',
                                 #placeholder=100
                                 )
            dataframe = gr.Dataframe(headers=["user_ids", "emails"],
                                    datatype=["str", "number"])
            button.click(export_csv, dataframe, csv)

        with gr.Column():
            recommendation = gr.Button("Найти пользователей")
            result = dataframe
            recommendation.click(recommender, [type1, type2, category_name, number_of_users], result)
    return interface
