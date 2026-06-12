"""
Модель трекера времени

Определяет проект, тикет, дату, время, вид работы 
@author Dmitry Abramov
"""
import pickle
import datetime
import re

import pytz
import tensorflow as tf
import numpy as np
import onnxruntime as ort

from . import DAYS_OF_WEEK, INT2TAG, TYPE_OF_WORK, MONTHS

# pylint: disable=too-many-branches
class TrackerModel:
    """
    Трек времени в формате для сохранения в БД

    На вход трек формулируется пользователем произвольно, на выходе в стандартизованном, 
    пригодном для сохранения формате

    Часть бота трекера времени, решает задачу NER(поиск именнованных сущностей)

    Модель построена на основе двунаправленных LSTM ячеек
    Имеет две ветки для определения тегов и классификации видов работы

    Первым слоем является - слой векторизации слов, который является словарем

    Пример использования объекта
    model = Tracker_mode(model_path, text_path) - сделать экземпляр класс, указав путь к моделям
    model() - инициализировать модель
    model.predict('Смарт 60 минут, обсуждение workflow с Романом') - получить словарь с результатом

        {
            'project': 'Проект'
            'ticket': 0
            'date': 12.07.2023, если даты нет в тексте, вернется сегодняшняя дата
            'spended_time': 60
            'work_type': 'Communication'
            'text': 'обсуждение workflow с Романом'
        }
    """
    def __init__(self, model_path='apps/tracker/data/model/model.onnx',
                 text_path='apps/tracker/data/model/tv_layer.pkl'):
        """
        :param model_path: str - путь к модели
        """
        self.model_path = model_path
        self.text_path = text_path
        self.model = None
        self.session = None

    def predict(self, text: str):
        """
        Предсказание на основе полученного сообщения

        :param text: str - полученное сообщение

        :return : dict
        {
            'project': str - Проект
            'ticket': int - Номер тикета, если не обнаружен в тексте, заполняется нулем,
            'date': str - Дата в формате 15.05.2023,
            'spended_time': int - Количество минут,
            'work_type': str - Один из восьми видов работ, определяется классификацией,
            'text': str - Заметка
        }
        """
        # Поиск даты
        date = re.search(r"(\d{2}[., /]\d{2}[., /]\d{2,4})", text)
        if date:
            text = re.sub(date.groups()[0], '', text)
        text = " ".join(text.split())
        # Словарь
        with open(self.text_path, "rb") as file:
            from_disk = pickle.load(file)
        # Настройка словаря
        text_vec = tf.keras.layers.TextVectorization.from_config(from_disk['config'])
        # Заполнение словаря
        text_vec.set_vocabulary(from_disk['weights'][0])
        prediction = self.session.run(None, {'inputs':  tf.cast(text_vec([text.lower()]),
                                                                dtype='float').numpy()})

        prediction = self._prepare_output(text, prediction)
        if date:
            prediction['date'] = date.groups()[0]
        return prediction

    def _init_model(self):
        """
        Загрузка модели
        """
        self.session = ort.InferenceSession(self.model_path,
                                        providers=['CUDAExecutionProvider',
                                                    'CPUExecutionProvider'])

    def _prepare_output(self, text, prediction) -> dict:
        """
        Подготовка данных для вывода
        Возвращает проект, время, тикет, дату, вид работ

        :param text: str - полученное сообщение
        :param prediciton: - np.array - теги для каждого слова

        :return : dict 
        
        {
            'project': str - Проект
            'ticket': int - Номер тикета, если не обнаружен в тексте, заполняется нулем,
            'date': str - Дата в формате 15.05.2023,
            'spended_time': int - Количество минут,
            'work_type': str - Один из восьми видов работ, определяется классификацией,
            'text': str - Заметка
        }
        """
        prediction_tags = np.argmax(np.array(prediction[0][0]), axis=1)

        splited_text = np.array(text.split(' '))
        if len(splited_text) > 25:
            splited_text = splited_text[:25]
        prediction_tags = np.array([INT2TAG.get(x, 7) for x in prediction_tags[:len(splited_text)]])

        # Удаление пунктуации
        splited_text = self._delete_punctuation(splited_text, prediction_tags)

        # Затраченное время
        minutes = splited_text[(prediction_tags == 'B-MIN') | (prediction_tags == 'I-MIN')]
        minutes = [int(minute) for minute in minutes if minute.isdigit()]
        # Если количество минут не найдено, будет возвращен ноль
        if len(minutes) > 0:
            time = minutes[0]
            del minutes
        else:
            time = 0

        # Номер тикета
        tickets = splited_text[(prediction_tags == 'B-TKT') | (prediction_tags == 'I-TKT')]
        tickets = [int(ticket) for ticket in tickets if ticket.isdigit()]
        if len(tickets) > 0:
            ticket = tickets[0]
            del tickets
        else:
            ticket = 0

        # Дата в формате 2 мая
        date = splited_text[(prediction_tags == 'B-DAT') | (prediction_tags == 'I-DAT')]
        # Дата с указанием года
        if len(date) == 3:
            month = MONTHS[date[1][:-1].lower()]
            date = date[0] + '.' + month + '.' + date[-1]
        # Дата без указания года
        elif len(date) == 2:
            month = MONTHS[date[1][:-1].lower()]
            date = date[0] + '.' + month + '.' + str(datetime.datetime.now().year)
            date = datetime.datetime.strptime(date, '%d.%m.%Y').strftime('%d.%m.%Y')
        else:
            try:
                date = self._date_extract(splited_text[prediction_tags == 'B-DAT'][0])
            except IndexError:
                # При отсутствии даты в тексте возвращается сегодняшняя дата
                date = datetime.datetime.now(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y')

        # Название проекта
        if 'B-PRO' in prediction_tags and 'I-PRO' in prediction_tags:
            project = splited_text[prediction_tags == 'B-PRO'][0] + ' ' + splited_text[prediction_tags == 'I-PRO'][0]
        elif 'B-PRO' in prediction_tags:
            project = splited_text[prediction_tags == 'B-PRO'][0]
        else:
            project = '-'

        # Словарь - результат
        result = {'project': project,
                  'ticket': ticket,
                  'date': date,
                  'spended_time': time,
                  'work_type': TYPE_OF_WORK[np.argmax(np.array(prediction[1][0]), axis=0)],
                  'text': ' '.join(splited_text[prediction_tags == '0'])}
        return result


    def _delete_punctuation(self, splited_text, prediction_tags):
        """
        Удаляет пунктуацию из всех тегов, кроме текста

        :param splited_text: np.array - сплитованный по пробелам текст
        :param prediction_tags: np.array - массив тегов

        :return : np.array - текст без знаков пунктуации
        """
        # Все теги, кроме текста
        punctuated_text = splited_text[prediction_tags != '0']
        # Индексы для тегов, не включая текст
        indexes = np.where(prediction_tags != '0')[0]
        # Удаление знаков пунктуации
        for index, text in zip(indexes, punctuated_text):
            splited_text[index] = re.sub(r'[^\w\s]', '', text)

        return splited_text


    def _date_extract(self, date):
        """
        Получение даты из текста

        Позволяет подготовить дату в форматах:
            1. 22.05.2023 (из бота данная возможность вырезана на момент 25 мая)
            2. 22/05/2023 (из бота данная возможность вырезана на момент 25 мая)
            3. Сегодня/вчера (получить дату)
            4. Получить дату на основе дня недели

            Рекомендация: вынести в отдельный объект, привести пример выхода
        """
        # Дата указана сегодняшним днем
        # (два варианта) первая русская/английская буква
        if date.title() == 'Сегодня' or date.title() == 'Cегодня':
            date = datetime.datetime.now(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y')
        elif date.title() == 'Вчера':
            date = datetime.datetime.now(pytz.timezone('Europe/Moscow')) - datetime.timedelta(days=1)
            date = date.strftime('%d.%m.%Y')
        else:
            # Введен день недели
            day = datetime.datetime.now(pytz.timezone('Europe/Moscow')).weekday() # Сегодняшний день недели
            week = 7
            cday = DAYS_OF_WEEK[date.title()] # День недели, который надо найти
            # Прошлая неделя - указан день с прошлой недели
            if datetime.datetime.now(pytz.timezone('Europe/Moscow')).weekday() <= DAYS_OF_WEEK[date.title()]:
                date = (datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(days=-week-day+cday))
                date = date.strftime('%d.%m.%Y')
            # Эта неделя
            else:
                day = datetime.datetime.now(pytz.timezone('Europe/Moscow')).weekday()
                cday = DAYS_OF_WEEK[date.title()]
                date = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(days=-day+cday)
                date = date.strftime('%d.%m.%Y')
        return date

    def __call__(self):
        self._init_model()
