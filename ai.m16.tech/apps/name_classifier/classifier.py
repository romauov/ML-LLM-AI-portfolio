"""
Валидатор имен
"""
import datetime
import pickle

import numpy as np
import tensorflow as tf

class NameClassifier():
    """
    Модель валидации имен
    """
    def __init__(self,
                 name_path='apps/name_classifier/data/models/name_model',
                 surname_path='apps/name_classifier/data/models/surname_model',
                 dict_path='apps/name_classifier/data/char2int'):
        self.name_path = name_path
        self.surname_path = surname_path
        self.dict_path = dict_path
        self.name_model = None
        self.surname_model = None
        self.char2int = None

    def init_data(self):
        """
            Инициализация модели и словаря
        """
        self.name_model = tf.keras.models.load_model(self.name_path)
        self.surname_model = tf.keras.models.load_model(self.surname_path)
        with open(self.dict_path, 'rb') as file:
            self.char2int = pickle.load(file)

    def prepare_input(self, name: str) -> str:
        """
            Подготовка имени 
            :param:
                name - str, Введенное имя
            :return:
                str - подготовленное имя
        """
        # Приведенеи к нижнему регистру
        lower_name = name.lower()
        # Кодирование
        preprocessed_name = np.array([self.char2int[ch] for ch in lower_name])
        # Усечение/добавление нулей
        preprocessed_name = preprocessed_name[:30] if len(
            preprocessed_name) >= 30 else \
            np.append(preprocessed_name, np.zeros(30 - len(preprocessed_name)))
        # Приведение к типу инт
        preprocessed_name = preprocessed_name.astype('int')
        # Добавление одной оси
        preprocessed_name = preprocessed_name.reshape(1, -1)
        return preprocessed_name

    def predict_name(self, name: str) -> dict:
        """
        Предсказание целевой метки с возвращением словаря
        :param:
            name: str - Подготовленное имя
        :return: {"name": "dsfdsf", "date": "y-m-d, H:M:S", "label": 0}
        """
        prepared_name = self.prepare_input(name)
        predicted_label = self.name_model.predict(prepared_name)

        return {'name': name,
                'date': datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
                'label': round(predicted_label[0][0])}

    def predict_surname(self, surname: str) -> dict:
        """
        Определение класса фамилии 
        :param:
            name: str - Подготовленная фамилия
        :return: {"surname": "dsfdsf", "date": "y-m-d, H:M:S", "label": 0}
        """
        prepared_surname = self.prepare_input(surname)
        predicted_label = self.surname_model.predict(prepared_surname)

        return {'surname': surname,
                'date': datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
                'label': round(predicted_label[0][0])}
