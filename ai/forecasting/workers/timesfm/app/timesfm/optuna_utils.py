"""
Подбор инференс-параметров TimesFM и оценка качества на holdout/CV.

@author Dmitry Avzalov
"""

import copy

import optuna
import pandas as pd

from app.logger import log
from app.timesfm.timesfm_model import TimesFMModel
from app.timesfm.utils import k_folds_cross_validation, mape


class Objective:
    def __init__(self, df: pd.Series, cfg: dict):
        self.df = df
        self.cfg = cfg
        self.best_cfg = None

    def __call__(self, trial):
        if trial.number != 0:
            self.cfg['timesfm']['model']['max_context'] = trial.suggest_categorical(
                'max_context', [64, 128, 256, 512, 1024]
            )
            self.cfg['timesfm']['model']['normalize_inputs'] = trial.suggest_categorical(
                'normalize_inputs', [True, False]
            )
            self.cfg['timesfm']['model']['use_continuous_quantile_head'] = trial.suggest_categorical(
                'use_continuous_quantile_head', [True, False]
            )
            self.cfg['timesfm']['train']['ew_lag'] = trial.suggest_int('ew_lag', 0, self.cfg['n_forecasts'])

        return k_folds_cross_validation(
            df=self.df,
            cfg=self.cfg,
            model_cfg=self.cfg['timesfm']['model'],
            train_cfg=self.cfg['timesfm']['train']
        )

    def callback(self, study, trial):
        if study.best_trial == trial:
            self.best_cfg = copy.deepcopy(self.cfg['timesfm'])


def timesfm_hyperparameters_tune(df: pd.Series, cfg: dict) -> (dict, float):
    log.info('start timesfm hyperparameter tuning')
    n_preds = cfg['n_forecasts']
    df_train, df_test = df[:-n_preds], df[-n_preds:]

    objective = Objective(df_train, copy.deepcopy(cfg))
    study = optuna.create_study(direction='minimize', study_name='timesfm')
    study.optimize(
        lambda trial: objective(trial),
        n_trials=cfg['optuna_n_trials'],
        callbacks=[objective.callback]
    )
    log.info('end timesfm hyperparameter tuning')

    preds = TimesFMModel(
        df=df_train,
        model_cfg=objective.best_cfg['model'],
        train_cfg=objective.best_cfg['train']
    ).predict(n_preds).values
    mape_at_test = round(mape(df_test.values, preds), 2)
    log.info(f'MAPE at test:{mape_at_test}')

    return objective.best_cfg, mape_at_test
