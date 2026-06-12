import copy

import optuna
import pandas as pd
import numpy as np

from app.theta.theta_model import ThetaModelWrapper
from app.utils import k_folds_cross_validation
from app.logger import log


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
            self.cfg['theta']['train']['theta'] = trial.suggest_float('theta', 1.0, 5.0)
            self.cfg['theta']['train']['use_mle'] = trial.suggest_categorical("use_mle", [True, False])
            self.cfg['theta']['train']['ew_lag'] = trial.suggest_int('ew_lag', 0, self.cfg['n_forecasts'])

        try:
            # time series cross validation
            mape = k_folds_cross_validation(
                df=self.df,
                k_folds=self.cfg['cross_validation_k_folds'],
                season_length=self.cfg['theta']['model']['period'],
                model_cls=ThetaModelWrapper,
                model_cfg=self.cfg['theta']['model'],
                train_cfg=self.cfg['theta']['train']
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
            self.best_cfg = copy.deepcopy(self.cfg['theta'])


def theta_hyperparameters_tune(df: pd.Series, cfg: dict) -> (dict, float):
    """
    Подбор лучших гиперпараметров.
    :param cfg: Config.
    :param df: dataframe.
    :return: tuple (dict с гиперпараметрами / MAPE)
    """
    log.info('start theta hyperparameter tuning')
    n_preds = cfg['n_forecasts']

    # откладываем тестовую выборку, которая не участвует в подборе гиперпараметров. Избегаем переобучения
    df_train, df_test = df[:-n_preds], df[-n_preds:]

    objective = Objective(df_train, copy.deepcopy(cfg))
    study = optuna.create_study(direction='minimize', study_name='theta')
    study.optimize(
        lambda trial: objective(trial),
        n_trials=cfg['optuna_n_trials'],
        callbacks=[objective.callback]
    )
    log.info('end theta hyperparameter tuning')

    preds = ThetaModelWrapper(
        df=df_train,
        model_cfg=objective.best_cfg['model'],
        train_cfg=objective.best_cfg['train']
    ).predict(n_preds).values
    y = df_test.values
    mape_at_test = round(np.mean(np.abs((y - preds) / y)) * 100, 2)

    log.info(f'MAPE at test:{mape_at_test}')

    return objective.best_cfg, mape_at_test
