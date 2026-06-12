import copy
import optuna
import pandas as pd
import numpy as np

from app.logger import log
from app.prophet.prophet_model import ProphetModel
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
            self.cfg['prophet']['model']['n_changepoints'] = trial.suggest_int('n_changepoints', 15, 50)
            self.cfg['prophet']['model']['changepoint_range'] = trial.suggest_float('changepoint_range', 0.8, 0.95,
                                                                                    log=True)
            self.cfg['prophet']['model']['seasonality_mode'] = trial.suggest_categorical(
                "seasonality_mode", ['additive', 'multiplicative']
            )
            self.cfg['prophet']['model']['seasonality_prior_scale'] = trial.suggest_float(
                'seasonality_prior_scale', 0.01, 10.0, log=True
            )
            self.cfg['prophet']['model']['holidays_prior_scale'] = trial.suggest_float(
                'holidays_prior_scale', 0.01, 10.0, log=True
            )
            self.cfg['prophet']['model']['changepoint_prior_scale'] = trial.suggest_float(
                'changepoint_prior_scale', 0.001, 0.5, log=True
            )
            self.cfg['prophet']['model']['holidays_mode'] = trial.suggest_categorical(
                'holidays_mode', ['additive', 'multiplicative']
            )
            self.cfg['prophet']['train']['ew_lag'] = trial.suggest_int('ew_lag', 0, self.cfg['n_forecasts'])

        # time series cross validation
        mape = k_folds_cross_validation(
            df=self.df,
            k_folds=self.cfg['cross_validation_k_folds'],
            season_length=self.cfg['prophet']['train']['period'],
            model_cls=ProphetModel,
            model_cfg=self.cfg['prophet']['model'],
            train_cfg=self.cfg['prophet']['train']
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
            self.best_cfg = copy.deepcopy(self.cfg['prophet'])


def prophet_hyperparameters_tune(df: pd.Series, cfg: dict) -> (dict, float):
    """
    Подбор лучших гиперпараметров.
    :param cfg: Config.
    :param df: dataframe.
    :return: tuple (dict с гиперпараметрами / MAPE)
    """
    log.info('start prophet hyperparameter tuning')
    n_preds = cfg['n_forecasts']

    # откладываем тестовую выборку, которая не участвует в подборе гиперпараметров. Избегаем переобучения
    df_train, df_test = df[:-n_preds], df[-n_preds:]

    objective = Objective(df_train, copy.deepcopy(cfg))
    study = optuna.create_study(direction='minimize', study_name='prophet')
    study.optimize(
        lambda trial: objective(trial),
        n_trials=cfg['optuna_n_trials'],
        callbacks=[objective.callback]
    )
    log.info('end prophet hyperparameter tuning')

    preds = ProphetModel(
        df=df_train,
        model_cfg=objective.best_cfg['model'],
        train_cfg=objective.best_cfg['train']
    ).predict(n_preds).values
    y = df_test.values
    mape_at_test = round(np.mean(np.abs((y - preds) / y)) * 100, 2)

    log.info(f'MAPE at test:{mape_at_test}')

    return objective.best_cfg, mape_at_test
