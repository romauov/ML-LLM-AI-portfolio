"""
Модуль модели Neuralprophet.
Включает в себя класс для работы с моделью и функцию подбора гиперпараметров.

@author Nikolay Zhabchikov
"""
import pandas as pd
from neuralprophet import NeuralProphet, set_log_level
import torch

from app.utils import exponential_weighting

set_log_level('ERROR')

DEVICE = 'gpu' if torch.cuda.is_available() else 'cpu'


class NeuralprophetModel:
    """
    Класс для работы моделью Neuralprophet.
    """

    def __init__(self, df: pd.DataFrame, model_cfg: dict, train_cfg: dict):
        self.model_cfg = model_cfg
        self.train_cfg = train_cfg
        self.df = df
        self.model = None

    def _prepare_data_for_predict(self, df: pd.DataFrame, n_preds: int) -> pd.DataFrame:
        """
        Создания датасета для предсказания.
        :param df: dataframe.
        :param n_preds: int, горизонт предсказания.
        :return: dataframe.
        """
        return self.model.make_future_dataframe(
            df,
            n_historic_predictions=True,
            periods=n_preds
        )

    @staticmethod
    def _handle_forecast(forecast: pd.DataFrame, n_preds: int) -> pd.Series:
        """
        Обработка предсказания модели в более удобный вид
        :param forecast: dataframe, предсказания модели.
        :param n_preds: int, горизонт предсказания.
        :return: dataframe в более удобном формате.
        """
        forecast = forecast[forecast['y'].isna()]
        yhats = ['yhat' + str(i) for i in range(1, n_preds + 1)]
        forecast.loc[:, 'pred'] = forecast[yhats].max(axis=1)
        forecast = forecast[['ds', 'pred']]
        forecast = forecast.set_index('ds')['pred']
        return forecast

    def _handle_macro_economic(self):
        """
        Добавление глобальных трендов макроэкономических показателей.
        :return:
        """
        macro_cols = self.df.loc[:, ~self.df.columns.isin(['ID', 'ds', 'y'])].columns.tolist()
        for macro_col in macro_cols:
            if self.df[macro_col].nunique() <= 1:
                self.df = self.df.drop(macro_col, axis=1)
            else:
                self.model.add_lagged_regressor(macro_col, n_lags=self.model_cfg['n_lags'])

    def predict(self, n_preds: int) -> pd.Series:
        """
        Предсказание для каждого уникального ID.
        :param n_preds: int, горизонт предсказания.
        :return:
        """

        self.df = self.df.reset_index().rename(columns={'index': 'ds', 0: 'y'})

        self.model_cfg['n_forecasts'] = n_preds
        self.model = NeuralProphet(**self.model_cfg, accelerator=DEVICE, trainer_config={"accelerator": DEVICE})
        self._handle_macro_economic()
        self.model.add_country_holidays('RUS')

        if self.train_cfg['ew_lag'] != 0:
            self.df = exponential_weighting(self.df, 'y', self.train_cfg['ew_lag'])
        self.model.fit(self.df, freq=self.train_cfg['freq'], minimal=True, epochs=self.train_cfg['n_epochs'])
        df = self._prepare_data_for_predict(self.df, n_preds)
        forecast = self.model.predict(df)
        forecast = self._handle_forecast(forecast, n_preds)
        return forecast
