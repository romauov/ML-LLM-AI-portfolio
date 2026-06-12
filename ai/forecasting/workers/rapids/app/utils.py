from typing import Type, TypeVar

import numpy as np
import numpy.typing as npt
import pandas as pd

from app.logger import log

ArimaModelT = TypeVar('ArimaModelT', bound='ArimaModel')


def get_cross_validation_split_ids(
        df: pd.Series,
        k_folds: int,
        season_length: int
) -> (npt.NDArray[np.int32], npt.NDArray[np.int32]):
    """
    Генератор. Возвращает фолды с train_ids и test_ids.
    :param df: ряд с индексами pd.DatetimeIndex и float значениями.
    :param k_folds: количество фолдов разбиения данных.
    :param season_length: размер одного сезона.
    :return: List[train_id], List[test_id]
    """

    if season_length:
        test_length = len(df) - (2 * season_length)
    else:
        log.indo('season_length is 0, set test_length 1/3 from dataframe')
        test_length = int(len(df) / 3)

    train_ids = df[:-test_length].index
    test_ids = np.array_split(df[-test_length:].index, k_folds)

    for fold_idx in range(k_folds):
        if fold_idx > 0:
            train_ids = train_ids.append(test_ids[fold_idx - 1])

        yield train_ids, test_ids[fold_idx]


def k_folds_cross_validation(
        df: pd.Series,
        k_folds: int,
        season_length: int,
        model_cls: Type[ArimaModelT],
        model_cfg: dict,
        train_cfg: dict
) -> float:
    """
    K_fold валидация временного ряда.
    :param df: ряд с индексами pd.DatetimeIndex и float значениями.
    :param k_folds: количество фолдов.
    :param season_length: размер одного сезона.
    :param model_cls: класс модели.
    :param model_cfg: конфигурация модели.
    :param train_cfg: конфигурации обучения
    """
    forecast_k_fold = []
    for train_idx, val_idx in get_cross_validation_split_ids(df, k_folds=k_folds, season_length=season_length):
        train_df, val_df = df.loc[train_idx], df.loc[val_idx]
        model = model_cls(train_df, model_cfg=model_cfg, train_cfg=train_cfg)

        preds = model.predict(len(val_df)).values
        y = val_df.values
        mape = np.mean(np.abs((y - preds) / y)) * 100

        forecast_k_fold.append(mape)

    return np.mean(forecast_k_fold)
