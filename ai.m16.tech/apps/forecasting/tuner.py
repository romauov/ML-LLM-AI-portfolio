"""
Настройка гиперпараметров модели NeuralProphet с использованием optuna

@author Dmitry Abramov
"""
from sklearn.metrics import mean_squared_error
from neuralprophet import NeuralProphet
import optuna


def objective(trial, data, steps):
    """
    Поиск гиперпараметров модели NeuralProphet с использованием optuna
    В качестве метрики оптимизации используется RMSE

    Принимает:
        trial: используется для совместимости с optuna
        data: pd.DataFrame
        steps: int - Количество шагов прогнозирования
    """
    changepoints_range = trial.suggest_float('changepoints_range', 0.8, 0.9, step=0.025)
    n_changepoints = trial.suggest_int('n_changepoints', 10, 50, step=10)
    seasonality_reg = trial.suggest_categorical('seasonality_reg', [0, 0.1, 1, 10])
    # trend_reg = trial.suggest_categorical('trend_reg', [0, 0.1, 1, 10])
    n_lags = trial.suggest_float('n_lags', 1.5, 3, step=0.2)
    n_forecasts = trial.suggest_categorical('n_forecasts', [steps])

    n_ar_layers = trial.suggest_int('n_ar_layers',  0, 3, step=1)
    n_ar_components = trial.suggest_int('n_ar_components', steps // 3, steps - 1)

    # n_lagged_reg_layers = trial.suggest_int('n_lagged_reg_layers',  0, 3, step=1)
    # n_lagged_reg_components = trial.suggest_int('n_lagged_reg_components', steps // 3, steps - 1)

    model = NeuralProphet(n_changepoints=n_changepoints,
                          changepoints_range=changepoints_range,
                          seasonality_reg=seasonality_reg,
                          # trend_reg=trend_reg,
                          n_lags=int(n_lags * steps),
                          n_forecasts=n_forecasts,
                          ar_layers=[n_ar_components] * n_ar_layers,
                          # lagged_reg_layers=[n_lagged_reg_components] * n_lagged_reg_layers
                         )

    model.add_country_holidays('RUS')

    _ = model.fit(data[:-steps])

    future = model.make_future_dataframe(data, periods=steps)
    forecast = model.predict(future)
    forecasted = model.get_latest_forecast(forecast).iloc[:, -1].values

    return mean_squared_error(data.y.values[-steps:], forecasted) ** 0.5


def _hyperparams_tuning(data, steps, path, n_trials=20):
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
    study = optuna.create_study()
    study.optimize(lambda trial: objective(trial, data=data, steps=steps), n_trials=n_trials)
    study.trials_dataframe().to_csv(path + '/hyperparams.csv', index=False)
    return study.best_params, study.best_value
