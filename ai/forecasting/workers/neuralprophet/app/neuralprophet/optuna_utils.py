import copy

import optuna
import pandas as pd
import numpy as np

from app.logger import log
from app.neuralprophet.neuralprophet_model import NeuralprophetModel
from app.utils import k_folds_cross_validation


class Objective:
    """
    Специальный класс для подбора гиперпараметров через optuna.
    Подбор гиперпараметров вынесен в класс для удобного callback.
    """

    def __init__(self, df: pd.DataFrame, cfg: dict):
        self.best_result = None
        self.best_cfg = None
        self._result = None
        self.df = df
        self.cfg = cfg

    def __call__(self, trial):
        # in first try always used default config
        if trial.number != 0:
            self.cfg['neuralprophet']['model']['yearly_seasonality'] = trial.suggest_categorical(
                "yearly_seasonality", [True, False]
            )
            self.cfg['neuralprophet']['model']['n_lags'] = trial.suggest_int('n_lags', 2, 13)
            self.cfg['neuralprophet']['model']['n_changepoints'] = trial.suggest_int('n_changepoints', 1, 100)
            self.cfg['neuralprophet']['model']['changepoints_range'] = trial.suggest_float(
                'changepoints_range', 0.7, 0.95
            )
            self.cfg['neuralprophet']['model']['trend_reg'] = trial.suggest_float('trend_reg', 0.0, 10)
            self.cfg['neuralprophet']['model']['trend_local_reg'] = trial.suggest_float('trend_local_reg', 0.0, 0.5)
            self.cfg['neuralprophet']['model']['seasonality_mode'] = trial.suggest_categorical(
                "seasonality_mode", ["additive", "multiplicative"]
            )
            self.cfg['neuralprophet']['model']['seasonality_reg'] = trial.suggest_float('seasonality_reg', 0.0, 10)
            self.cfg['neuralprophet']['model']['seasonality_local_reg'] = trial.suggest_float(
                'seasonality_local_reg', 0.0, 0.5
            )
            self.cfg['neuralprophet']['model']['ar_reg'] = trial.suggest_float('ar_reg', 0.0, 10)
            self.cfg['neuralprophet']['model']['normalize'] = trial.suggest_categorical(
                "normalize", ['off', 'minmax', 'standardize', 'soft', 'soft1']
            )
            self.cfg['neuralprophet']['model']['learning_rate'] = trial.suggest_float('learning_rate', 1e-5, 1e-1)
            self.cfg['neuralprophet']['train']['ew_lag'] = trial.suggest_int('ew_lag', 0, self.cfg['n_forecasts'])

        # time series cross validation
        try:
            mape = k_folds_cross_validation(
                df=self.df,
                k_folds=self.cfg['cross_validation_k_folds'],
                season_length=self.cfg['neuralprophet']['train']['period'],
                model_cls=NeuralprophetModel,
                model_cfg=self.cfg['neuralprophet']['model'],
                train_cfg=self.cfg['neuralprophet']['train'],
                target_col='y'
            )
        except Exception as e:
            log.info(f"Trial failed with params {trial.params}: {e}")
            mape = float('inf')

        return mape

    def callback(self, study, trial):
        """
        callback функция
        :param study: внутренний объект optuna.study.Study
        :param trial: внутренний объект optuna.trial
        :return: MAPE
        """
        if study.best_trial == trial:
            self.best_cfg = copy.deepcopy(self.cfg['neuralprophet'])


def np_hyperparameters_tune(df: pd.DataFrame, cfg: dict) -> (dict, float):
    """
    Подбор лучших гиперпараметров.
    :param cfg: Config.
    :param df: dataframe.
    :return: tuple (dict с гиперпараметрами / MAPE)
    """
    log.info('start neuralprophet hyperparameter tuning')
    n_preds = cfg['n_forecasts']
    # откладываем тестовую выборку, которая не участвует в подборе гиперпараметров. Избегаем переобучения
    df_train, df_test = df[:-n_preds], df[-n_preds:]

    objective = Objective(df_train, copy.deepcopy(cfg))

    study = optuna.create_study(direction='minimize', study_name='neuralprophet')
    study.optimize(
        lambda trial: objective(trial),
        n_trials=cfg['optuna_n_trials'],
        callbacks=[objective.callback]
    )
    log.info('end neuralprophet hyperparameter tuning')
    preds = NeuralprophetModel(
        df=df_train,
        model_cfg=objective.best_cfg['model'],
        train_cfg=objective.best_cfg['train']
    ).predict(n_preds).values
    y = df_test['y'].values
    mape_at_test = round(np.mean(np.abs((y - preds) / y)) * 100, 2)

    log.info(f'MAPE at test:{mape_at_test}')

    return objective.best_cfg, mape_at_test
