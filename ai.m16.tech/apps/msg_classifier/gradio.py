"""
Демостраница работы квалификатора сообщений на основе Chat GPT

@author Sergei Romanov
"""
import requests
from requests.auth import HTTPBasicAuth

import gradio as gr

def get_classifier_reply(method, text):
    """
    Получение ответа от квалификатора
    """
    result = requests.post('https://ai.m16.tech/api/msg_classifier',
                        json={
                            "method": method,
                            "text": text
                            },
                        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                        timeout=30
                        )
    result = list(result.json().values())

    return result[0]

def gr_msg_classifier_interface():
    """
    Интерфейс градио
    """
    interface =  gr.Interface(fn = get_classifier_reply,
                              inputs=[
                                  gr.Radio(
                                      ["chat_gpt", "giga_chat", "merged"],
                                      value = 'giga_chat', label="method", info="Метод классификации"),
                                  gr.Textbox(
                                      label="text",
                                      info="сообщение пользователя",
                                      placeholder="добрый день можно получит прайс лист")
                                  ],
                              outputs=['text'],
                              examples=[
                                  ["chat_gpt", "добрый день можно получит прайс лист"],
                                  ["giga_chat", "вложений нет 01.02.2024, 13:18, \"Рассылка ЦОПа\""],
                                  ["merged", "Здравствуйте"],
                                  ["chat_gpt", "Добрый день. Напишите пожалуйста состав. И если есть декларации  \
                                      \n\n -- Отправлено из Mail.ru для Android"],
                                  ["giga_chat", "Добрый день.Мы свами уже общались.\
                                      Мы начинаем работать с образцов.Елена Борисовна."]
                                  ],
                              allow_flagging="never"
                              )

    return interface
