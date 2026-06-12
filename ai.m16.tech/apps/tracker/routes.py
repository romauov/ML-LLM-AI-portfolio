"""
Веб сервис трекера времени

@author Dmitry Abramov
"""
import json

from flask import request

from . import blueprint
from .classifier import TrackerModel

# Загрузка и инициализация модели
model = TrackerModel()
model()

@blueprint.route('/tracker', methods=['POST'])
def track():
    """
    Апи трекера времени

    Принимает json формата {'text': 'Смарт 60 минут, обсуждение workflow с Романом'}

    На основе полученного сообщения возвращает json
    {
        'project': 'Проект'
        'ticket': 0
        'date': 12.07.2023, если даты нет в тексте, вернется сегодняшняя дата
        'spended_time': 60
        'work_type': 'Communication'
        'text': 'обсуждение workflow с Романом'
    }
    """
    request_data = request.get_json()

    try:
        result = model.predict(request_data['text'])
    except TypeError:
        result = {'error': f"В тексте возможно находится двойное указание времени/проекта/тикета "
                           f"Введенный текст: {request_data['text']}"}

    return json.dumps(result, ensure_ascii=False)
