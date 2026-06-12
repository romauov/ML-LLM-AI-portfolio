"""
Модуль модели Theta.
Включает в себя класс для работы с моделью и функцию подбора гиперпараметров.

@author Nikolay Zhabchikov
"""

from statsmodels.tsa.forecasting.theta import ThetaModel
from statsmodels.tsa.stattools import adfuller
import pandas as pd

from app.utils import exponential_weighting


class ThetaModelWrapper:
    """
    Класс для работы моделью statsmodels.tsa.forecasting.theta.ThetaModel
    """

    def __init__(self, df: pd.Series, model_cfg: dict, train_cfg: dict):
        self.model_cfg = model_cfg
        self.train_cfg = train_cfg
        self.df = df

    @staticmethod
    def _need_difference(endog: pd.Series) -> bool:
        adf, _, _, _, critical_values, _ = adfuller(endog)
        if adf > critical_values['5%']:
            return True
        else:
            return False

    def predict(self, n_preds: int) -> pd.Series:
        """
        Предсказание для каждого уникального ID.
        :param n_preds: int, горизонт предсказания.
        :return:
        """
        df = self.df.copy()
        df = df.asfreq(self.train_cfg['freq'])
        if self.train_cfg['ew_lag'] != 0:
            df = exponential_weighting(df, self.train_cfg['ew_lag'])

        fitted_model = ThetaModel(
            endog=df,
            period=self.model_cfg['period'],
            deseasonalize=True,
            use_test=False,
            method='auto',
            difference=self._need_difference(df)
        ).fit(use_mle=self.train_cfg['use_mle'])
        forecast = fitted_model.forecast(steps=n_preds, theta=self.train_cfg['theta'])
        forecast.name = 'pred'

        return forecast
