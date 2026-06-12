"""
Демостраница работы генератора карточек пользователя

@author Sergei Romanov
"""
import requests
from requests.auth import HTTPBasicAuth

import gradio as gr

def card_generator(site, userid=None, user_email=None):
    """
    Генерация карточки по сайту и userid
    """
    result = requests.post('https://ai.m16.tech/api/user_profile',
                        json={
                            "site": site,
                            "userid": userid,
                            "user_email": user_email
                            },
                        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                        timeout=30
                        )
    result = list(result.json().values())[0]
    with open("user_card.md", "w", encoding="utf-8") as text_file:
        text_file.write(result)

    return gr.File.update(value="user_card.md", visible=True), result

def gr_user_card_interface():
    """
    Интерфейс демо-страницы
    """
    interface =  gr.Interface(fn = card_generator,
                              inputs=[
                                  gr.Radio(["meatinfo", "fishretail"], value = 'meatinfo', label="site", info="Сайт"),
                                  gr.Number(label="userid", info="id клиента", precision=0),
                                  gr.Textbox(label="user_email", info="эл.почта клиента")
                                  ],
                              outputs=[gr.File(), gr.Markdown()],
                              examples=[
                                  ["meatinfo", 228618, ""],
                                  ["fishretail", 3075, ""],
                                  ["meatinfo", None, "somebody@mail.ru"]
                                  ],
                              allow_flagging="never"
                              )
    return interface
