import copy

import optuna
import pandas as pd
import numpy as np

from app.utils import k_folds_cross_validation
from app.arima.arima_model import ArimaModel
from app.logger import log


class Objective:
    """
    Специальный класс для подбора гиперпараметров через optuna.
    Подбор гиперпараметров вынесен в класс для удобного callback.
    """

    def __init__(self, df, cfg):
        self.best_result = None
        self.best_cfg = None
        self._result = None
        self.df = df
        self.cfg = cfg

    def __call__(self, trial):
        # in first try always used default config
        if trial.number != 0:
            self.cfg['arima']['model']['p'] = trial.suggest_int('p', 1, 4)
            self.cfg['arima']['model']['P'] = trial.suggest_int('P', 0, 2)
            self.cfg['arima']['model']['Q'] = trial.suggest_int('Q', 0, 2)
            self.cfg['arima']['model']['fit_intercept'] = trial.suggest_categorical("fit_intercept", [True, False])

            if all(self.cfg['arima']['model'][key] == 0 for key in ['p', 'P', 'Q', 'fit_intercept']):
                log.info('At least one parameter among p, q, P, Q and fit_intercept must be non-zero. set "p" = 1')
                self.cfg['arima']['model']['p'] = 1

        # time series cross validation
        try:
            mape = k_folds_cross_validation(
                df=self.df,
                k_folds=self.cfg['cross_validation_k_folds'],
                season_length=self.cfg['arima']['model']['s'],
                model_cls=ArimaModel,
                model_cfg=self.cfg['arima']['model'],
                train_cfg=self.cfg['arima']['train']
            )
        except Exception as e:
            log.info(f"Trial failed with params {trial.params}: {e}")
            mape = float('inf')

        self._result = mape
        return mape

    def callback(self, study, trial):
        """
        callback функция
        :param study: внутренний объект optuna.study.Study
        :param trial: внутренний объект optuna.trial
        :return: MAPE
        """
        if study.best_trial == trial:
            self.best_result = self._result
            self.best_cfg = copy.deepcopy(self.cfg['arima'])


def arima_hyperparameters_tune(df: pd.Series, cfg: dict) -> (dict, float):
    """
    Подбор лучших гиперпараметров.
    :param cfg: Config.
    :param df: ряд с индексами pd.DatetimeIndex и float значениями.
    :return: tuple (dict с гиперпараметрами / MAPE)
    """
    log.info('start ARIMA hyperparameter tuning')
    n_preds = cfg['n_forecasts']
    # откладываем тестовую выборку, которая не участвует в подборе гиперпараметров. Избегаем переобучения
    df_train, df_test = df[:-n_preds], df[-n_preds:]

    objective = Objective(df_train, copy.deepcopy(cfg))
    study = optuna.create_study(direction='minimize', study_name='arima')
    study.optimize(
        lambda trial: objective(trial),
        n_trials=cfg['optuna_n_trials'],
        callbacks=[objective.callback],
    )
    log.info('end ARIMA hyperparameter tuning')
    preds = ArimaModel(
        df=df_train,
        model_cfg=objective.best_cfg['model'],
        train_cfg=objective.best_cfg['train']
    ).predict(n_preds).values
    y = df_test.values
    mape_at_test = round(np.mean(np.abs((y - preds) / y)) * 100, 2)

    log.info(f'MAPE at test:{mape_at_test}')

    return objective.best_cfg, mape_at_test
