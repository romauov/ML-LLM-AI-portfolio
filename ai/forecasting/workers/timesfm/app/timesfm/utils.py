"""
Утилиты для валидации и оценки качества прогноза TimesFM.

@author Dmitry Avzalov
"""

import numpy as np
import pandas as pd

from app.timesfm.timesfm_model import TimesFMModel


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if not np.any(mask):
        return float('inf')
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def iter_cv_split_ids(df: pd.Series, k_folds: int, season_length: int):
    if season_length:
        test_length = len(df) - (2 * season_length)
    else:
        test_length = int(len(df) / 3)

    test_length = max(test_length, k_folds)
    if test_length <= 0 or test_length >= len(df):
        raise ValueError('Cannot split data for cross validation')

    train_ids = df[:-test_length].index
    test_ids = np.array_split(df[-test_length:].index, k_folds)
    for fold_idx in range(k_folds):
        if fold_idx > 0:
            train_ids = train_ids.union(test_ids[fold_idx - 1])
        yield train_ids, test_ids[fold_idx]


def k_folds_cross_validation(df: pd.Series, cfg: dict, model_cfg: dict, train_cfg: dict) -> float:
    forecast_k_fold = []
    for train_idx, val_idx in iter_cv_split_ids(
            df=df,
            k_folds=cfg['cross_validation_k_folds'],
            season_length=cfg['timesfm']['train']['period']
    ):
        train_df, val_df = df.loc[train_idx], df.loc[val_idx]
        preds = TimesFMModel(train_df, model_cfg=model_cfg, train_cfg=train_cfg).predict(len(val_df)).values
        fold_mape = mape(val_df.values, preds)
        forecast_k_fold.append(fold_mape)

    return float(np.mean(forecast_k_fold))
