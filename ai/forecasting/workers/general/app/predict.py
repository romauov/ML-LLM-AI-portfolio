from typing import Optional, Type, Callable

import pandas as pd
import json

from app.exponential_smoothing.exponential_smoothing_model import ExponentialSmoothingModel
from app.exponential_smoothing.optuna_utils import es_hyperparameters_tune
from app.prophet.prophet_model import ProphetModel
from app.prophet.optuna_utils import prophet_hyperparameters_tune
from app.theta.optuna_utils import theta_hyperparameters_tune
from app.theta.theta_model import ThetaModelWrapper
from app.logger import log


def _get_model_cls_and_tune_func_by_name(model: str) -> (
        Optional[Type[ExponentialSmoothingModel]],
        Callable
):
    match model:
        case 'Exponential smoothing':
            return ExponentialSmoothingModel, es_hyperparameters_tune
        case 'Prophet':
            return ProphetModel, prophet_hyperparameters_tune
        case 'ThetaModel':
            return ThetaModelWrapper, theta_hyperparameters_tune
        case _:
            raise KeyError('Неизвестное название модели')


def predict_with_hyperparameter_tuning(df_json: str, cfg: dict, forecasting_date: str, model_name: Optional[str]) -> str:
    log.info(f'start predict and tuning {model_name}')
    df = pd.read_json(df_json, encoding='utf-8', orient='records')
    df['ds'] = pd.to_datetime(df['ds'], unit='ms')

    model, hyperparameters_tune_f = _get_model_cls_and_tune_func_by_name(model_name)

    result = []
    for cat in df['ID'].unique().tolist():
        df_ = df[df['ID'] == cat].copy()
        df_.set_index('ds', inplace=True)

        log.info(f'predict for category: {cat}')
        best_cfg, mape = hyperparameters_tune_f(df=df_['y'], cfg=cfg)
        preds = model(df_['y'], best_cfg['model'], best_cfg['train']).predict(cfg['n_forecasts'])

        result.append({
            "model": model_name,
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
