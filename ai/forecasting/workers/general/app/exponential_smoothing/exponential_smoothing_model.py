"""
Модуль модели экспоненциального сглаживания.
Включает в себя класс для работы с моделью и функцию подбора гиперпараметров.

@author Nikolay Zhabchikov
"""

from statsmodels.tsa.api import ExponentialSmoothing
import pandas as pd

from app.utils import exponential_weighting


class ExponentialSmoothingModel:
    """
    Класс для работы моделью statsmodels.tsa.api.ExponentialSmoothing.
    """

    def __init__(self, df: pd.Series, model_cfg: dict, train_cfg: dict):
        self.model_cfg = model_cfg
        self.train_cfg = train_cfg
        self.df = df

    def predict(self, n_preds: int) -> pd.Series:
        """
        :param n_preds: горизонт предсказания.
        :return:
        """
        df = self.df.copy()
        if self.train_cfg['ew_lag'] != 0:
            df = exponential_weighting(df, self.train_cfg['ew_lag'])

        model = ExponentialSmoothing(df, **self.model_cfg).fit()
        forecast = model.forecast(n_preds)
        forecast.name = 'pred'

        return forecast
