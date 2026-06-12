import copy

import optuna
import pandas as pd
import numpy as np

from app.exponential_smoothing.exponential_smoothing_model import ExponentialSmoothingModel
from app.logger import log
from app.utils import k_folds_cross_validation


class Objective:
    """
    Специальный класс для подбора гиперпараметров через optuna.
    Подбор гиперпараметров вынесен в класс для удобного callback.
    """

    def __init__(self, df: pd.Series, cfg: dict):
        self.best_result = None
        self.best_cfg = None
        self._result = None
        self.df = df
        self.cfg = cfg

    def __call__(self, trial):
        # in first try always used default config
        if trial.number != 0:
            self.cfg['exponential_smoothing']['model']['trend'] = trial.suggest_categorical(
                "trend", ["add", "mul", "additive", "multiplicative"]
            )
            self.cfg['exponential_smoothing']['model']['seasonal'] = trial.suggest_categorical(
                "seasonal", ["add", "mul", "additive", "multiplicative"]
            )
            self.cfg['exponential_smoothing']['model']['initialization_method'] = trial.suggest_categorical(
                "initialization_method", [None, "estimated", "heuristic"]
            )
            self.cfg['exponential_smoothing']['model']['damped_trend'] = trial.suggest_categorical(
                "damped_trend", [True, False]
            )
            self.cfg['exponential_smoothing']['train']['ew_lag'] = trial.suggest_int('ew_lag', 0,
                                                                                     self.cfg['n_forecasts'])

        # time series cross validation
        mape = k_folds_cross_validation(
            df=self.df,
            k_folds=self.cfg['cross_validation_k_folds'],
            season_length=self.cfg['exponential_smoothing']['model']['seasonal_periods'],
            model_cls=ExponentialSmoothingModel,
            model_cfg=self.cfg['exponential_smoothing']['model'],
            train_cfg=self.cfg['exponential_smoothing']['train']
        )

        return mape

    def callback(self, study, trial):
        """
        callback функция
        :param study: внутренний объект optuna.study.Study
        :param trial: внутренний объект optuna.trial
        :return: MAPE
        """
        if study.best_trial == trial:
            self.best_cfg = copy.deepcopy(self.cfg['exponential_smoothing'])


def es_hyperparameters_tune(df: pd.Series, cfg: dict) -> (dict, float):
    """
    Подбор лучших гиперпараметров.
    :param cfg: Config.
    :param df: dataframe.
    :return: tuple (dict с гиперпараметрами / MAPE)
    """
    log.info('start exponential smoothing hyperparameter tuning')
    n_preds = cfg['n_forecasts']
    # откладываем тестовую выборку, которая не участвует в подборе гиперпараметров. Избегаем переобучения
    df_train, df_test = df[:-n_preds], df[-n_preds:]

    objective = Objective(df_train, copy.deepcopy(cfg))
    study = optuna.create_study(direction='minimize', study_name='exponential smoothing')
    study.optimize(
        lambda trial: objective(trial),
        n_trials=cfg['optuna_n_trials'],
        callbacks=[objective.callback]
    )
    log.info('end exponential smoothing hyperparameter tuning')

    preds = ExponentialSmoothingModel(
        df=df_train,
        model_cfg=objective.best_cfg['model'],
        train_cfg=objective.best_cfg['train']
    ).predict(n_preds).values
    y = df_test.values
    mape_at_test = round(np.mean(np.abs((y - preds) / y)) * 100, 2)

    log.info(f'MAPE at test:{mape_at_test}')

    return objective.best_cfg, mape_at_test
