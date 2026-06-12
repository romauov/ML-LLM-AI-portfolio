"""
Интерфейс демо страницы валидатора ответов 

@author Dmitry Abramov
"""
import gradio as gr

import requests
from requests.auth import HTTPBasicAuth

def validator(text):
    """
    :params:
        text: str - введенный текст
    :return:
        list - класс 
    """
    result = requests.post('https://ai.m16.tech/api/answer_validator',
                        json={"text": text},
                        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                        timeout=10)

    return list(result.json().values())


def gr_validator_interface():
    """
    Валидатора ответов 
    """
    return gr.Interface(title="Трекер",
                        fn=validator,
                        inputs=[
                            gr.Textbox(placeholder="текст")
                        ],
                        outputs=[gr.Textbox()]
                        )
