"""
Метрики mae и mape для оценки модели на валидационном наборе данных

@author Dmitry Abramov
"""
import pandas as pd
import numpy as np


def mape(actual, predicted, index1, path):
    """
    Расчет метрики MAPE

    actual: np.array - реальные данные
    predicted: np.array - спрогнозированные данные
    index1: list(pd.datetime) - индексы - даты
    path: str - путь директории результатов
    
    Возвращает:
        mape_df: pd.DataFrame() - MAPE по датам
            schema: 
                [('Дата', pd.datetime64),
                ('mape': float)]
        mape_df.mape.mean(): float - средняя MAPE
    """
    mape_df = pd.DataFrame(np.abs((actual - predicted) / actual) * 100,
                           columns=['mape'])
    mape_df.index = index1
    mape_df = mape_df.reset_index(names='Дата')
    mape_df.to_csv(path + '/mape_df.csv', index=False)
    return mape_df, mape_df.mape.mean()


def mae(actual, predicted, index1, path):
    """
    Расчет метрики MAPE

    actual: np.array - реальные данные
    predicted: np.array - спрогнозированные данные
    index1: list(pd.datetime) - индексы - даты
    path: str - путь директории результатов
    
    Возвращает:
    mae_df: pd.DataFrame() - MAE по датам
        schema: 
            [('Дата', pd.datetime64),
            ('mae': float)]
    mae_df.mape.mean(): float - средняя MAE
    """
    mae_df = pd.DataFrame(abs(predicted - actual), columns=['mae'])
    mae_df.index = index1
    mae_df = mae_df.reset_index(names='Дата')
    mae_df.to_csv(path + '/mae_df.csv', index=False)
    return mae_df, mae_df.mae.mean()


def mae_gl(actual, predicted):
    """
    Расчет mae для моделирования нескольких временных рядов
    
    Принимает:
    actual: np.array[float] - реальные данные
    predicted: np.array[float] - реальные данные

    Возвращает:
    np.array[float] - mae для каждого прогноза
    """
    return np.abs(predicted - actual)


def mape_gl(actual, predicted):
    """
    Расчет mape для моделирования нескольких временных рядов

    Принимает:
    actual: np.array[float] - реальные данные
    predicted: np.array[float] - реальные данные

    Возвращает:
    np.array[float] - mape для каждого прогноза
    """
    return np.abs((actual - predicted) / actual) * 100
