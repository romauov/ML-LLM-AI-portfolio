"""
Модуль модели prophet.
Включает в себя класс для работы с моделью и функцию подбора гиперпараметров.

@author Nikolay Zhabchikov
"""

import pandas as pd
from prophet import Prophet

from app.utils import exponential_weighting


class ProphetModel:
    """
    Класс для работы c моделью Prophet.
    """

    def __init__(self, df: pd.Series, model_cfg: dict, train_cfg: dict):
        self.model_cfg = model_cfg
        self.train_cfg = train_cfg
        self.df = df

    def predict(self, n_preds: int) -> pd.Series:
        """
        Предсказание для каждого уникального ID.
        :param n_preds: int, горизонт предсказания.
        :return:
        """
        df = self.df.copy()
        if self.train_cfg['ew_lag'] != 0:
            df = exponential_weighting(df, self.train_cfg['ew_lag'])

        # конвертация в pd.Dataframe
        df.name = 'y'
        df = df.rename_axis('ds').reset_index()

        model = Prophet(**self.model_cfg, uncertainty_samples=0)
        model.fit(df, algorithm='LBFGS')
        future_df = model.make_future_dataframe(periods=n_preds, freq=self.train_cfg['freq'])

        forecast = model.predict(future_df)
        # конвертация в pd.Series
        forecast = forecast[['ds', 'yhat']][-n_preds:].set_index('ds')['yhat']
        forecast.name = 'pred'

        return forecast
