"""
Pipeline квалификатора лидов Spacy

@author Dmitry Avzalov, Yaroslav Koltashev
"""
from os.path import join
# pylint: disable=import-error
from spacy_dir.model_spacy import TextClassifer


def spacy_prediction_pipeline(text_list, preprocessing_data):
    """
    Пайплайн прогнозирования с помощью модели Spacy.

    Принимает список текстовых данных и функцию предварительной обработки данных.
    Создает экземпляр модели TextClassifier с указанными параметрами и загружает сохраненную модель.
    Применяет функцию предварительной обработки данных к списку текстовых данных.
    Выполняет прогнозирование с использованием модели и возвращает результаты.

    :param text_list: Список текстовых данных для прогнозирования.
    :type text_list: list
    :param preprocessing_data: Функция предварительной обработки данных.
    :type preprocessing_data: function

    :return: Прогнозированные результаты.
    :rtype: list
    """
    models = TextClassifer(models_path=join('apps', 'leads_classification', 'spacy_dir', 'best_model'), show_info=False)
    data_to_predict = preprocessing_data(text_list)
    prediction = models.predict(data_to_predict)

    return prediction
