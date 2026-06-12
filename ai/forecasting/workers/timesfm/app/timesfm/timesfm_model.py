"""
Класс-обертка над TimesFM для подготовки ряда и получения прогноза.

@author Dmitry Avzalov
"""
import os

import pandas as pd
import numpy as np
import timesfm


class TimesFMModel:
    _model = None
    _model_name = None

    def __init__(self, df: pd.Series, model_cfg: dict, train_cfg: dict):
        self.df = df
        self.model_cfg = model_cfg
        self.train_cfg = train_cfg

    @classmethod
    def _get_model(cls, model_name: str):
        if cls._model is None or cls._model_name != model_name:
            cls._model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
                model_name,
                cache_dir=os.getenv('HF_HOME'),
                local_files_only=True
            )
            cls._model_name = model_name
        return cls._model

    def _prepare_input_series(self) -> np.ndarray:
        series = self.df.copy()
        if self.train_cfg.get('ew_lag', 0) != 0:
            series = series.ewm(self.train_cfg['ew_lag']).mean()
        return series.values.astype(np.float32)

    def predict(self, n_preds: int) -> pd.Series:
        model = self._get_model(self.model_cfg['model_name'])
        model.compile(
            timesfm.ForecastConfig(
                max_context=min(self.model_cfg['max_context'], len(self.df)),
                max_horizon=n_preds,
                normalize_inputs=self.model_cfg['normalize_inputs'],
                use_continuous_quantile_head=self.model_cfg['use_continuous_quantile_head'],
                infer_is_positive=self.model_cfg['infer_is_positive']
            )
        )
        point_forecast, _ = model.forecast(
            horizon=n_preds,
            inputs=[self._prepare_input_series()]
        )

        start = self.df.index.max() + pd.tseries.frequencies.to_offset(self.train_cfg['freq'])
        forecast_index = pd.date_range(start=start, periods=n_preds, freq=self.train_cfg['freq'])
        return pd.Series(point_forecast[0][:n_preds], index=forecast_index)
