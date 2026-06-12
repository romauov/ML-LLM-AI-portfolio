"""
Интерфейс для апи трекера

@author Dmitry Abramov
"""
import gradio as gr
import requests
from requests.auth import HTTPBasicAuth

def tracker(text):
    """
    :params:
        text: str - введенный текст
    :return:
        list
    """
    result = requests.post('https://ai.m16.tech/api/tracker',
                        json={"text": text},
                        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                        timeout=10)

    return list(result.json().values())

def gr_tracker_interface():
    """
    Интерфейс для взаимодействия с ботом
    """
    return gr.Interface(title="Трекер",
                        fn=tracker,
                        inputs=[
                            gr.Textbox(placeholder="текст")
                        ],
                        outputs=[gr.Text(label="project"),
                                 gr.Text(label="ticket"),
                                 gr.Text(label="date"),
                                 gr.Text(label="spended_time"),
                                 gr.Text(label="work_type"),
                                 gr.Text(label="text")
                        ],
                        )
