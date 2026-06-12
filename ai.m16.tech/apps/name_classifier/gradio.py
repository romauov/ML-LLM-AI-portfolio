"""
Валидатор фамилий
"""
import gradio as gr
import requests
from requests.auth import HTTPBasicAuth

examples = [
    ['Иванов'],
    ['132g12'],
    ['Чайник'],
]


def surname(text: str) -> str:
    """
    Определение фамилии
    :params: 
        text: str - введенный текст
    :return:
        str 

    """
    res = requests.get(f'https://ai.m16.tech/api/surname_classifier?name={text}',
                       auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                       timeout=10)
    data = res.json()
    return "Прошло проверку" if data['label'] == 1 else "Не прошло проверку"


def gr_surname_interface():
    """
        Интерфес для валидатора фамилий 
    """
    return gr.Interface(title="Валидатор фамилий",
                        fn=surname,
                        examples=examples,
                        inputs=[
                            gr.Textbox(placeholder="фамилия")
                        ],
                        outputs=[gr.Text(label="Класс")
                        ],
                        )
