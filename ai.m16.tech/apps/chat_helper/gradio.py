"""
Демостраница работы цифрового помощника на основе ChatGPT

@author Sergei Romanov
"""
import requests
from requests.auth import HTTPBasicAuth

import gradio as gr

def get_helper_reply(user_promt, table_id, text_id, from_id):
    """
    Получение ответа от помощника
    """
    result = requests.post('https://ai.m16.tech/api/chat_helper',
                        json={
                            "user_promt": user_promt,
                            "table_id": table_id,
                            "text_id": text_id,
                            "from_id": from_id
                              },
                        auth=HTTPBasicAuth('user', '{{API_PASSWORD}}'),
                        timeout=30
                        )
    result = list(result.json().values())

    return result[0], result[1]

def gr_chat_helper_interface():
    """
    Интерфейс градио
    """
    interface =  gr.Interface(fn = get_helper_reply,
                              inputs=[
                                  gr.Textbox(
                                      label="user_promt",
                                      info="вопрос для цифрового помощника",
                                      placeholder="нужны цены на вырезку"),
                                  gr.Textbox(
                                      label="table_id",
                                      info="id гугл-таблицы с прайслистом",
                                      placeholder="12Fj1RcAr0yB6PLtq_S6MH27I0wVV0Fgo8_QkACrovvo"),
                                  gr.Textbox(
                                      label="text_id",
                                      info="id гугл-документа с регламентом",
                                      placeholder="1L32jhOaPfgOwIRSj5FPy1JxCQ22T1cBlR6IStDGhDGE"),
                                  gr.Number(
                                      label="from_id",
                                      info="id клиента, откоторого приходит запрос")
                                  ],
                              outputs=['text', 'text'],
                              examples=[
                                  ["нужны цены на вырезку", \
                                      "12Fj1RcAr0yB6PLtq_S6MH27I0wVV0Fgo8_QkACrovvo", \
                                          "1L32jhOaPfgOwIRSj5FPy1JxCQ22T1cBlR6IStDGhDGE", 100500],
                                  ["откуда отгружается голяшка?", \
                                      "12Fj1RcAr0yB6PLtq_S6MH27I0wVV0Fgo8_QkACrovvo", \
                                          "1L32jhOaPfgOwIRSj5FPy1JxCQ22T1cBlR6IStDGhDGE", 100500],
                                  ["какая продукция у вас есть?", \
                                      "12Fj1RcAr0yB6PLtq_S6MH27I0wVV0Fgo8_QkACrovvo", \
                                          "1L32jhOaPfgOwIRSj5FPy1JxCQ22T1cBlR6IStDGhDGE", 100500],
                                  ["нужно предложение по всей продукции", \
                                      "12Fj1RcAr0yB6PLtq_S6MH27I0wVV0Fgo8_QkACrovvo", \
                                          "1L32jhOaPfgOwIRSj5FPy1JxCQ22T1cBlR6IStDGhDGE", 100500],
                                  ["пришли свои контакты", \
                                      "12Fj1RcAr0yB6PLtq_S6MH27I0wVV0Fgo8_QkACrovvo", \
                                          "1L32jhOaPfgOwIRSj5FPy1JxCQ22T1cBlR6IStDGhDGE", 100500]
                                  ],
                              allow_flagging="never"
                              )

    return interface
