"""
Квалификатор ответов 

@author Dmitry Abramov
"""
import pickle
import re
import openpyxl

import tensorflow as tf
import numpy as np
import onnxruntime as ort

from . import CLASSES, CLASSES_CODES


class AnswerValidator:
    """
    Модель валидации ответов на сообщения
    """
    def __init__(self,
                 model_path='apps/answer_validator/data/model/model.onnx',
                 tv_path='apps/answer_validator/data/model/tv_layer.pkl'):
        self.model_path = model_path
        self.tv_path = tv_path
        self.session = None

    def predict(self, text):
        """
        Определение класса
        """
        with open(self.tv_path, "rb") as file:
            from_disk = pickle.load(file)

        tv_layer = tf.keras.layers.TextVectorization.from_config(from_disk['config'])
        tv_layer.set_vocabulary(from_disk['weights'][0])

        prediction = self.session.run(None, {'inputs':  tf.cast(tv_layer([self._text_preprocessing(text).lower()]),
                                                                dtype='int32').numpy()})

        pred_class = CLASSES[int(np.array(prediction).argmax())]
        class_code = CLASSES_CODES[pred_class]

        prediction = prediction[0][0].astype(float)
        sorted_pred_args = prediction.argsort()[::-1]
        prediction = np.sort(prediction)[::-1]

        classification = {
                            CLASSES[_class]: {
                                'id': CLASSES_CODES[CLASSES[_class]], 
                                'prob': prediction[index]
                                }
                            for index, _class in enumerate(sorted_pred_args)
                         }
        return {
                "class": pred_class,
                "class_name": class_code,
                "classification": classification
                }

    def _init_session(self):
        """
        Инициализация сессии
        """
        self.session = ort.InferenceSession(self.model_path,
                                            providers=['CUDAExecutionProvider',
                                                       'CPUExecutionProvider'])

    def _text_preprocessing(self, text):
        text = text[:text.find('Original Message')] if 'Original Message' in text else text

        text = openpyxl.utils.escape.unescape(text)
        text = re.sub(r"[a-zA-Z]+\w*\d\w*", '', str(text).lower())
        text = re.sub(r'[^а-яА-ЯёЁ\d+]', ' ', text)

        # Удаление цитирования
        text = text[:text.find('отправлено')] if 'отправлено' in text else text
        text = text[:text.find('с уважением')] if 'с уважением' in text else text

        # Замена цифр на решетку
        text = re.sub(r'\d+', '#', text)
        # text = ['email@' if '@' in word else word for word in text.split()]
        return ' '.join(text.split() if set(text.split()) != {'#'} else [''])

    def __call__(self):
        self._init_session()
