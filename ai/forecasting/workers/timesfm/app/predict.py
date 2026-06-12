"""
Функции инференса и сериализации результата прогноза TimesFM.

@author Dmitry Avzalov
"""

import json
from typing import Optional

import pandas as pd

from app.logger import log
from app.timesfm.optuna_utils import timesfm_hyperparameters_tune
from app.timesfm.timesfm_model import TimesFMModel


def predict_with_hyperparameter_tuning(df_json: str, cfg: dict, forecasting_date: Optional[str]) -> str:
    log.info('start predict and tuning TimesFM')
    df = pd.read_json(df_json, encoding='utf-8', orient='records')
    df['ds'] = pd.to_datetime(df['ds'], unit='ms')

    result = []
    for cat in df['ID'].unique().tolist():
        df_ = df[df['ID'] == cat].copy()
        df_.set_index('ds', inplace=True)

        log.info(f'predict for category: {cat}')
        best_cfg, mape = timesfm_hyperparameters_tune(df=df_['y'], cfg=cfg)
        preds = TimesFMModel(df_['y'], best_cfg['model'], best_cfg['train']).predict(cfg['n_forecasts'])

        result.append({
            "model": 'TimesFM',
            "forecasting_date": forecasting_date,
            "forecast_horizon": cfg["n_forecasts"],
            "frequency": cfg["freq"],
            "ID": cat,
            "dates": preds.index.strftime('%Y-%m-%d').tolist(),
            "preds": preds.values.tolist(),
            "mape": mape
        })
    response = json.dumps({"result": result})
    return response
