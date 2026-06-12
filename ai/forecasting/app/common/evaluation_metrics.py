"""
Метрики оценки моделей.

@author Nikolay Zhabchikov
"""
import numpy as np


def mean_absolute_percentage_error(y_true, y_pred):
    """
    Расчет средней абсолютной ошибки в процентах (MAPE).
    :param y_true: Истинные значения y.
    :param y_pred: предсказанные значения y.
    :return: float, значение ошибки
    """
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100
