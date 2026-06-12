"""
Модель сети для определения продукции

@author Sergey Goncharov
"""
import gradio as gr
import requests
from requests.auth import HTTPBasicAuth

models = ['cointegrated/rubert-tiny', 'cointegrated/rubert-tiny2']
examples = [
    ['cointegrated/rubert-tiny', 'говядиналопатка говяжья разделка отличного качествазвоните по ценам договоримся'],
    ['cointegrated/rubert-tiny', 'индейка фарш мясной цена 85'],
    ['cointegrated/rubert-tiny', 'свинина обрезь гост мясная цена 150']]


def product(model: str, text: str) -> list:
    """
    Определение продукции
    """
    res = requests.post(
        'https://ai.m16.tech/api/product/product-detect',
        data={'text': text, 'model': model}, timeout=10,
        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}')
    )
    data = res.json()
    return [val['value'] + " / " + str(val['proba']) for val in data.values()]


def gr_interface():
    """
    Интерфейс для модели определения продукции
    """
    return gr.Interface(title="Модель сети для определения продукции",
                        fn=product,
                        examples=examples,
                        inputs=[
                            gr.Dropdown(models),
                            gr.Textbox(placeholder="текст продукции"),
                        ],
                        outputs=[
                            gr.Text(label="Вид"),
                            gr.Text(label="Разруб"),
                            gr.Text(label="Терм. сост"),
                            gr.Text(label="Гост"),
                            gr.Text(label="Ту"),
                        ],
                        )
