"""
Модуль модели ARIMA.
Включает в себя класс для работы с моделью и функцию подбора гиперпараметров.

@author Nikolay Zhabchikov
"""
import gc

import numpy as np
import pandas as pd
import platform

from app.logger import log

if platform.system() == 'Windows':
    log.warning('cuml.tsa.arima.ARIMA model is not supported by Windows operating system')


class ArimaModel:
    """
    Класс для работы c моделью Sarimax.
    """

    def __init__(self, df: pd.Series, model_cfg: dict, train_cfg: dict):
        self.model_cfg = model_cfg
        self.train_cfg = train_cfg
        self.df = df

    def get_forecasting_date_index(self, train_df: pd.Series, n_preds: int) -> pd.DatetimeIndex:
        return pd.date_range(start=train_df.index.max(), periods=n_preds + 1, freq=self.train_cfg['freq'])[1:]

    @staticmethod
    def add_noise_to_constant_groups(series: pd.Series, noise_std: float = 0.5, min_group_size: int = 5) -> pd.Series:
        result = series.copy()
        groups = (series != series.shift(1)).cumsum()
        group_sizes = groups.map(groups.value_counts())
        constant_mask = group_sizes >= min_group_size

        # Добавляем шум
        noise = np.round(np.random.normal(0, noise_std, len(series)), 2)
        result[constant_mask] += noise[constant_mask]

        return result

    def predict(self, n_preds: int) -> pd.Series:
        """
        Предсказание для каждого уникального ID.
        :param n_preds: int, горизонт предсказания.
        :return:
        """

        import cudf
        from cuml.tsa.arima import ARIMA
        from cuml.common import logger as cuml_logger

        cuml_logger.set_level(cuml_logger.level_enum.error)

        df = self.df

        df = self.add_noise_to_constant_groups(df)
        cu_df = cudf.from_pandas(df)  # преобразование из pandas в cuda dataframe
        cu_model = ARIMA(
            endog=cu_df,
            order=(self.model_cfg['p'], self.model_cfg['d'], self.model_cfg['q']),
            seasonal_order=(self.model_cfg['P'], self.model_cfg['D'], self.model_cfg['Q'], self.model_cfg['s']),
            fit_intercept=self.model_cfg['fit_intercept'],
            simple_differencing=self.model_cfg['simple_differencing']
        )
        cu_fitted_model = cu_model.fit(method=self.train_cfg['method'])
        cu_forecast = cu_fitted_model.forecast(n_preds)
        forecast = cu_forecast.to_pandas()  # преобразование из cuda в pandas dataframe
        forecast.index = self.get_forecasting_date_index(df, n_preds)
        forecast.name = 'pred'

        del cu_model, cu_fitted_model, cu_forecast, cu_df
        gc.collect()

        return forecast
