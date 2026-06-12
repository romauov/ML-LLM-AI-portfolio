from typing import Optional
import pandas as pd
import json

from app.arima.arima_model import ArimaModel
from app.arima.optuna_utils import arima_hyperparameters_tune
from app.logger import log


def predict_with_hyperparameter_tuning(df_json: str, cfg: dict, forecasting_date: Optional[str]) -> str:
    log.info('start predict and tuning')
    df = pd.read_json(df_json, encoding='utf-8', orient='records')
    df['ds'] = pd.to_datetime(df['ds'], unit='ms')

    result = []
    for cat in df['ID'].unique().tolist():
        df_ = df[df['ID'] == cat].copy()
        df_.set_index('ds', inplace=True)

        log.info(f'predict for category: {cat}')
        best_cfg, mape = arima_hyperparameters_tune(df=df_['y'], cfg=cfg)
        preds = ArimaModel(df_['y'], best_cfg['model'], best_cfg['train']).predict(cfg['n_forecasts'])

        result.append({
            "model": "Arima",
            "forecasting_date": forecasting_date,
            "forecast_horizon": cfg["n_forecasts"],
            "frequency": cfg["arima"]["train"]["freq"],
            "ID": cat,
            "dates": preds.index.strftime('%Y-%m-%d').tolist(),
            "preds": preds.values.tolist(),
            "mape": mape
        })
    response = json.dumps({"result": result})
    return response
