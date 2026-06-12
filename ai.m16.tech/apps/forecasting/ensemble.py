"""
Ансамблирование модели NeuralProphet - обучается n_ensebmles моделей, результат усредняется

Приведен код для последовательного и параллельного обучения
Используется последовательный способ обучения / инференса ансамбля

Для использования параллельного подойдут пакеты
    (при решении проблемы с очисткой памяти между запусками): joblib, dask

@author Dmitry Abramov
"""
import io

from PIL import Image
from neuralprophet import NeuralProphet
import pandas as pd
import matplotlib.pyplot as plt


def _parallel_ensemble(data, params):
    """
    Параллельное обучение ансамбля с помощью joblib
    
    data: pd.DataFrame, данные для обучения
      schema: 
        [('ds', pd.datetime64),
         ('y': float)]
    params: dict, наилучшая комбинация параметров, найденная с помощью optuna
    
    Возвращает обученную модель NeuralProphet
    

    Код для запуска:
    models = Parallel(n_jobs=-1)(delayed(_ensemble_prophet)(data, best_params) for data in ensemble_data)
    """
    model = NeuralProphet(n_changepoints=params['n_changepoints'],
                          changepoints_range=params['changepoints_range'],
                          seasonality_reg=params['seasonality_reg'],
                          trend_reg=params['trend_reg'],
                          n_lags=params['n_lags'],
                          n_forecasts=params['n_forecasts'],
                          ar_layers=[params['n_ar_components']] *
                          params['n_ar_layers'],
                          lagged_reg_layers=[params['n_lagged_reg_components']] * params['n_lagged_reg_layers'])

    model.add_country_holidays('RUS')
    _ = model.fit(data)
    return model


def _parallel_ensemble(model, data, steps):
    """
    Параллельный инференс ансамбля с помощью joblib
    
    data: pd.DataFrame, данные для обучения
      schema: 
        [('ds', pd.datetime64),
         ('y': float)]
    params: dict, наилучшая комбинация параметров, найденная с помощью optuna
    
    Возвращает обученную модель NeuralProphet
    

    predictions = Parallel(n_jobs=-1)(delayed(_inference_ensemble)(model, data, steps) for model in models)
    """
    future = model.make_future_dataframe(data, periods=steps)
    model.restore_trainer()
    forecast = model.predict(future)
    return model.get_latest_forecast(forecast).set_index('ds').iloc[:, -1]


def _sequential_ensemble(data, params, n_ensebmles, path):
    """
    Последовательное обучение / инференс модели

    data: pd.DataFrame, данные для обучения
      schema: 
        [('ds', pd.datetime64),
         ('y': float)]
    params: dict, наилучшая комбинация параметров, найденная с помощью optuna
    n_ensebmles: int - количество моделей в ансамбле

    Возвращает:
        forecasting: pd.DataFrame - результат прогнозирования
            schema: 
                [('Дата', pd.datetime64),
                ('Прогноз': float)]
        PIL.Image - прогноз модели на всех данных и в будущее 
    """
    models = []
    forecasting = []

    if not n_ensebmles:
        n_ensebmles = 1

    # Последовательное обучение ансамбля
    for _ in range(n_ensebmles):
        model = NeuralProphet(n_changepoints=params['n_changepoints'],
                              changepoints_range=params['changepoints_range'],
                              seasonality_reg=params['seasonality_reg'],
                              # trend_reg=params['trend_reg'],
                              n_lags=int(params['n_lags'] * params['n_forecasts']),
                              n_forecasts=params['n_forecasts'],
                              ar_layers=[params['n_ar_components']] * params['n_ar_layers'],
                              # lagged_reg_layers=[params['n_lagged_reg_components']] * params['n_lagged_reg_layers']
                              )
        model.add_country_holidays('RUS')
        _ = model.fit(data)

        models.append(model)

    # Создание датасета для прогнозирования в будущее
    future = models[0].make_future_dataframe(
        data, periods=params['n_forecasts'], n_historic_predictions=True)

    # Прогноз полученный первой моделью в ансамбле
    model = models[0].highlight_nth_step_ahead_of_each_forecast(
        params['n_forecasts'])
    model.plot(model.predict(future), plotting_backend='matplotlib')

    # Сохранение диаграммы в директорию
    plt.savefig(path + '/model_forecast_plot.png',
                format='png', bbox_inches='tight')

    # Диаграмма для gradio
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight')

    # Последовательный инференс моделей - получение прогнозов
    for model in models:
        forecast = model.predict(future)
        forecasting.append(model.get_latest_forecast(
            forecast).set_index('ds').iloc[:, -1])

    forecasting = pd.concat(forecasting, axis=1).mean(axis=1)
    forecasting = forecasting.reset_index()
    forecasting.columns = ['Дата', 'Прогноз']
    return forecasting, Image.open(img_buf)


def _sequential_ensemble_glocal(data, params, path):
    """
    Последовательное обучение / инференс модели для прогнозирования нескольких временных рядов
        с использованием NeuralProphet

    data: pd.DataFrame, данные для обучения
      schema: 
        [('ds', pd.datetime64),
         ('ID', str),
         ('y': float)]
    params: dict, наилучшая комбинация параметров, найденная с помощью optuna
    n_ensebmles: int - количество моделей в ансамбле

    Возвращает:
        pd.DataFrame schema: [('ds': datetime64), (col, float)] - датафрейм включает в себя дату, столбцы со 
        спрогнозированными значениями, названия столбцов соответствует входному файлу
    """
    train = data.melt(id_vars='ds',
                      var_name='ID',
                      value_name='y')

    model = NeuralProphet(**params)
    model.add_country_holidays('RUS')
    _ = model.fit(train)

    # Создание датасета для прогнозирования в будущее
    future = model.make_future_dataframe(train,
                                         periods=params['n_forecasts'],
                                         n_historic_predictions=True)
    forecast = model.predict(future)

    # Построение прогноза по кажому временному ряду
    for _id in forecast.ID.unique():
        model = model.highlight_nth_step_ahead_of_each_forecast(
            params['n_forecasts'])
        model.plot(forecast[forecast.ID == _id], plotting_backend='matplotlib')
        plt.title(f"Прогноз на {_id} на {params['n_forecasts']} отсчетов")
        # Сохранение диаграммы в директорию
        plt.savefig(path + f'/model_forecast_plot_{_id}.png', format='png', bbox_inches='tight')

    forecast_result = pd.DataFrame()

    # Построение прогноза по кажому временному ряду
    for col in forecast.ID.unique():
        forecast_result[col] = model.get_latest_forecast(forecast[forecast.ID == col])[
            'origin-0'][-params['n_forecasts']:].values
    forecast_result['ds'] = forecast.ds[-params['n_forecasts']:].values

    return forecast_result
