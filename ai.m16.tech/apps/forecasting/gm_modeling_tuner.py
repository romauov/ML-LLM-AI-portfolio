"""
Настройка гиперпараметров модели NeuralProphet с использованием optuna 
для прогнозирования производства

@author Dmitry Abramov
"""
from sklearn.metrics import mean_squared_error
from neuralprophet import NeuralProphet
import optuna
import numpy as np


def rmse(actual, frst):
    """
    Расчет rmse при оценке гиперпараметров модели
    
    Принимает:
    actual: np.array[float] - реальные данные
    frst: np.array[float] - реальные данные

    Возвращает:
    float - rmse при проверке гиперпараметров модели
    """
    return mean_squared_error(actual, frst) ** 0.5


def objective(trial, train_data, test_data, steps):
    """
    Поиск гиперпараметров модели NeuralProphet с использованием optuna
    В качестве метрики оптимизации используется RMSE

    Принимает:
        trial: используется для совместимости с optuna
        train_data: pd.DataFrame
        test_data: pd.DataFrame
        steps: int - Количество шагов прогнозирования
    """
    changepoints_range = trial.suggest_float('changepoints_range', 0.8, 0.98, step=0.03)
    n_changepoints = trial.suggest_int('n_changepoints', 10, 50, step=10)
    seasonality_reg = trial.suggest_categorical('seasonality_reg', [0, 0.001, 0.01, 0.1, 1, 10])
    trend_reg = trial.suggest_categorical('trend_reg', [0, 0.001, 0.01, 0.1, 1])
    n_lags = trial.suggest_categorical('n_lags', [1.3, 1.5, 1.7, 1.9, 2.1, 2.2, 2.4, 2.7, 2.8])
    n_forecasts = trial.suggest_categorical('n_forecasts', [steps])
    ar_reg = trial.suggest_categorical('ar_reg', [0, 0.001, 0.01, 0.1, 1])

    n_ar_layers = trial.suggest_int('n_ar_layers',  0, 3, step=1)
    n_ar_components = trial.suggest_int('n_ar_components', n_forecasts, int(n_lags * steps) - 2)

    modeling = trial.suggest_categorical('modeling', ['local'])

    model = NeuralProphet(n_changepoints=n_changepoints,
                          changepoints_range=changepoints_range,
                          seasonality_reg=seasonality_reg,
                          trend_reg=trend_reg,
                          ar_reg=ar_reg,
                          n_lags=int(n_lags * steps),
                          n_forecasts=n_forecasts,
                          ar_layers=[n_ar_components] * n_ar_layers,
                          trend_global_local=modeling,
                          season_global_local=modeling,
                          drop_missing=True
                          )
    model.add_country_holidays('RUS')

    _ = model.fit(train_data)

    future = model.make_future_dataframe(train_data, periods=n_forecasts, n_historic_predictions=50)
    forecast = model.predict(future)


    errors = [rmse(test_data[test_data.ID == _id].y.values,
                   forecast.loc[forecast.ID == _id, f'yhat{steps}'][-steps:].values)
              for _id in forecast.ID.unique()]

    return np.mean(errors)


def _hyperparams_tuning_glocal(data, steps, path, n_trials=20):
    """
    Настройка гиперпараметров модели NeuralProphet с использованием optuna

    Принимает:
        data: pd.DataFrame
        steps: int - количество шагов прогнозирования
        path: str - путь директории результатов для сохранения логов 
            настройки гиперпараметров
        n_trials: int - количество итераций настройки гиперпараметров

    Возвращает:
        study.best_params: dict - лучшая комбинация гиперпараметров  
        study.best_value: float - лучшая метрика RMSE

    Сохраняет в {path}/hyperparams.csv запуски настройки гиперпараметров
    """
    train_melt = data[:-steps].melt(id_vars='ds',
                                    var_name='ID', value_name='y')
    test_melt = data[-steps:].melt(id_vars='ds', var_name='ID', value_name='y')

    study = optuna.create_study()
    study.optimize(lambda trial: objective(trial, train_data=train_melt,
                   test_data=test_melt, steps=steps), n_trials=n_trials)
    study.trials_dataframe().to_csv(path + '/hyperparams.csv', index=False)

    params = {'n_changepoints': study.best_params['n_changepoints'],
              'changepoints_range': study.best_params['changepoints_range'],
              'seasonality_reg': study.best_params['seasonality_reg'],
              'trend_reg': study.best_params['trend_reg'],
              'ar_reg': study.best_params['ar_reg'],
              'n_lags': int(study.best_params['n_forecasts'] * study.best_params['n_lags']),
              'n_forecasts': study.best_params['n_forecasts'],
              'ar_layers': [study.best_params['n_ar_components']] * study.best_params['n_ar_layers'],
              'trend_global_local': study.best_params['modeling'],
              'season_global_local': study.best_params['modeling']
              }

    return params, study.best_value
