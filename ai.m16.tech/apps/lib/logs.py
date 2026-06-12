"""
Логирование сообщений

@author Sergey Goncharov
"""
import datetime
import os

from sentry_sdk import capture_message

FILE_LOG_PATH = 'data/logs/python-message.log'


def send_message_to_file(text: str):
    """
    Запись сообщения в файл

    :param text:
    :return:
    """
    now = datetime.datetime.now()
    text = str(now) + " - " + text + "\n"

    with open(FILE_LOG_PATH, 'a', encoding="utf-8") as file:
        file.write(text)


def message(text: str):
    """
    Отправка сообщения в sentry или в файл

    :param text:
    :return:
    """
    if os.environ['MODE'] == 'PROD':
        capture_message(text)
    else:
        send_message_to_file(text)
