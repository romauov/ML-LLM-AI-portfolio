"""
Пайплайн автоматического прогнозирования с использованием NeuralProphet

@author Dmitry Abramov
"""
import os
import datetime
from pathlib import Path
from warnings import filterwarnings

import pandas as pd
from neuralprophet import NeuralProphet, set_log_level
import gradio as gr
from PIL import Image

from .tuner import _hyperparams_tuning
from .forecasting_visualization import validation_plot, forecasting_plot, forecasting_plot_bins
from .metrics import mape, mae
from .ensemble import _sequential_ensemble
from .db_logging import exist_checker, insert_row, result_getting


def _data_loader(ds_col, y_col, temp_file, sheet_name):
    """
    Загрузка данных из переданного файла:
    Загрузка данных по указанным колонкам ds_col, y_col

    Поддерживаемые форматы: .xlsx, .xls, .csv

    Принимает:
        ds_col: str - Название колонки с датой
        y_col: str - Название колонки, которую нужно спрогнозировать
        temp_file -

    Возвращает:
        pd.DataFrame
            schema:
                    [('ds', pd.datetime64),
                    ('y': float)]
    """
    if sheet_name == '':
        sheet_name = 0

    _, file_extension = os.path.splitext(temp_file.name)

    if file_extension in ('.xlsx', '.xls'):
        try:
            df = pd.read_excel(temp_file.name,
                               sheet_name=sheet_name)
        except ValueError as e:
            raise gr.Error("Ошибка при чтении файла. Проверьте название листа/таблицы") from e
    else:
        df = pd.read_csv(temp_file.name)

    try:
        df = df[[ds_col, y_col]]
    except ValueError as e:
        raise gr.Error("Ошибка при чтении файла. Кажется, колонки не найдены") from e

    df = df.rename(columns={ds_col: 'ds', y_col: 'y'})
    return df


def _validation_forecasting(data, params):
    """
    Проверочное прогнозирование:
    Построение модели на основе найденных гиперпараметров

    Принимает:
        data: pd.DataFrame - данные
        params: dict - лучшая комбинация гиперпараметров

    Возвращает:
        forecast - pd.DataFrame
    """
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

    _ = model.fit(data[:-12])
    future = model.make_future_dataframe(data[:-params['n_forecasts']], periods=params['n_forecasts'])
    forecast = model.predict(future)
    forecast = model.get_latest_forecast(forecast).iloc[:, -1].values
    return forecast

# pylint: disable=too-many-arguments
def pipeline(ds_col, y_col, steps, validation_steps, trials,
             temp_file, n_ensemble, date_border=None, sheet_name=0, years=10, use_save=True):
    """
    Пайплайн для автоматического прозирования с использованием NeuralProphet:
    1. _data_loader - Загрузка данных
    2. _hyperparams_tuning - Поиск наилучшей комбинации гиперпараметров
    3. _validation_forecasting - Прогнозирование для проверки
    4. mae и mape - расчет метрик на проверочном наборе данных
    5. _sequential_ensemble - Последовательное обучение ансамбля из n_ensemble моделей NeuralProphet
    6. validation_plot - Результат прогнозирования при валидации
    7. forecasting_plot - Результат прогнозирования
    8. forecasting_plot_bins - Столбчатая диаграмма результатов прогнозирования
    9. exist_checker - Проверка наличия прогнозирования с такими же параметрами/файлом
    10. insert_row - Запись в БД параметров успешной итерации прогнозирования

    Принимает:
        ds_col: str - Название колонки с датой
        y_col: str - Название колонки, которую нужно спрогнозировать
        steps: int - Количество шагов прогнозирования
        validation_steps: int - Количество шагов прогнозирования на валидации
        trials: int - Количество итераций настройки гиперпараметров
        temp_file: Файл
        n_ensemble: int - Количество моделей в ансамбле

    Возвращает:
        validation_img: диграмма на валидации
        forecasting_img: прогнозирование
        mae_df: pd.DataFrame - ошибка mae по датам 
            schema: 
                [('Дата', pd.datetime64),
                ('mae': float)]
        mae_mean: float - средняя mae
        mape_df: pd.DataFrame - ошибка mape по датам
            schema: 
                    [('Дата', pd.datetime64),
                    ('mape': float)]
        mape_mean: float - средняя mape
        forecast: pd.DataFrame - прогнозирование по датам
            schema:
                    [('Дата', pd.datetime64),
                    ('Прогноз_{y_col}': float)]
    """
    filterwarnings('ignore')
    set_log_level("ERROR")

    if use_save == 'Да':
        # Проверка генерации с такими же параметрами
        exist_status, exist_dir, _id = exist_checker(ds_col,
                                                     y_col,
                                                     steps,
                                                     validation_steps,
                                                     trials,
                                                     temp_file.name.split('/')[-1],
                                                     n_ensemble,
                                                     date_border,
                                                     sheet_name,
                                                     years)

        if exist_status:
            mae_df = pd.read_csv(exist_dir + '/mae_df.csv')
            mape_df = pd.read_csv(exist_dir + '/mape_df.csv')
            validation_img = Image.open(exist_dir + '/validation_plot.png')
            forecast_img = Image.open(exist_dir + '/forecast_plot.png')
            bins_img = Image.open(exist_dir + '/bins_plot.png')
            model_forecast_img = Image.open(exist_dir + '/model_forecast_plot.png')
            forecast = pd.read_csv(exist_dir + '/forecast.csv')

            forecast.to_csv("output.csv", index=False)
            return (_id, exist_dir, gr.File.update(value="output.csv", visible=True), validation_img, forecast_img,
                    bins_img, model_forecast_img, mae_df, mae_df.mae.mean(), mape_df, mape_df.mape.mean(), forecast)

    path = f"apps/forecasting_result/{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_{y_col}_{steps}_st/"

    Path(path).mkdir(parents=True, exist_ok=True)

    data = _data_loader(ds_col, y_col, temp_file, sheet_name)

    try:
        data['ds'] = pd.to_datetime(data.ds)
    except ValueError as e:
        raise gr.Error(f"Ошибка при преобразовании колонки {ds_col} в формат даты") from e

    if date_border:
        data = pd.concat([data[data.ds < pd.to_datetime(date_border)],
                          data[data.ds >= pd.to_datetime(date_border)].iloc[:steps, :]],
                         ignore_index=True)

    data = data[data.ds.dt.year >= datetime.datetime.now().year - years].reset_index(drop=True)

    best_params, _ = _hyperparams_tuning(data, validation_steps, path, trials)

    valid_forecast = _validation_forecasting(data, best_params)

    # Расчет метрика MAE и MAPE
    mae_df, mae_mean = mae(data[-validation_steps:].y.values,
                           valid_forecast,
                           data[-validation_steps:].ds.dt.date.values,
                           path)
    mape_df, mape_mean = mape(data[-validation_steps:].y.values,
                              valid_forecast,
                              data[-validation_steps:].ds.dt.date.values,
                              path)

    best_params['n_forecasts'] = steps

    forecast, model_forecast_img = _sequential_ensemble(data, best_params, n_ensemble, path)

    validation_img = validation_plot(data[-validation_steps:].y.values,
                                     valid_forecast,
                                     data[-validation_steps:].ds.values,
                                     y_col,
                                     validation_steps,
                                     mape_mean, mae_mean, path)

    forecasting_img = forecasting_plot(forecast, y_col, steps, path)
    bins_img = forecasting_plot_bins(forecast, path)

    forecast['Дата'] = forecast['Дата'].dt.date
    forecast = forecast.rename(columns={'Прогноз': f'Прогноз на {y_col}'})

    forecast.to_csv(path + "forecast.csv", index=False)

    _id = insert_row(ds_col, y_col, steps, validation_steps, trials,
                    temp_file.name.split('/')[-1], n_ensemble, date_border, sheet_name, years, path)

    forecast.to_csv("output.csv", index=False)
    return (_id, path, gr.File.update(value="output.csv", visible=True), validation_img, forecasting_img,
            bins_img, model_forecast_img, mae_df, mae_mean, mape_df, mape_mean, forecast)


def get_result(_id, path=None):
    """
    Загрузка результатов с помощью id запуска прогнозирования / пути к директории
    """
    if path:
        try:
            mae_df = pd.read_csv(path + '/mae_df.csv')
            mape_df = pd.read_csv(path + '/mape_df.csv')
            validation_img = Image.open(path + '/validation_plot.png')
            forecast_img = Image.open(path + '/forecast_plot.png')
            bins_img = Image.open(path + '/bins_plot.png')
            model_forecast_img = Image.open(path + '/model_forecast_plot.png')
            forecast = pd.read_csv(path + '/forecast.csv')
        except FileNotFoundError as e:
            raise gr.Error(f'Путь не найден либо файлы повреждены при сохранении: {e}') from e

    if _id and not path:
        exist_status, exist_dir = result_getting(_id)
        if exist_status:
            mae_df = pd.read_csv(exist_dir + '/mae_df.csv')
            mape_df = pd.read_csv(exist_dir + '/mape_df.csv')
            validation_img = Image.open(exist_dir + '/validation_plot.png')
            forecast_img = Image.open(exist_dir + '/forecast_plot.png')
            bins_img = Image.open(exist_dir + '/bins_plot.png')
            model_forecast_img = Image.open(exist_dir + '/model_forecast_plot.png')
            forecast = pd.read_csv(exist_dir + '/forecast.csv')
        else:
            raise gr.Error('Результат не найден по этому id')

    forecast.to_csv("output.csv", index=False)
    return (gr.File.update(value="output.csv", visible=True), validation_img, forecast_img, bins_img,
            model_forecast_img, mae_df, mae_df.mae.mean(), mape_df, mape_df.mape.mean(), forecast)
