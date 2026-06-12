"""
Пайплайн автоматического прогнозирования нескольких временных рядов с использованием NeuralProphet

@author Dmitry Abramov
"""
import os
import datetime
from pathlib import Path
import shutil
from warnings import filterwarnings

import pandas as pd
from neuralprophet import NeuralProphet, set_log_level
import gradio as gr

from .gm_modeling_tuner import _hyperparams_tuning_glocal
from .forecasting_visualization import validation_plot, forecasting_plot, forecasting_plot_bins
from .metrics import mae_gl, mape_gl
from .ensemble import _sequential_ensemble_glocal
from .db_logging import exist_checker, insert_row, result_getting


def _data_loader_glocal(ds_col, temp_file, sheet_name):
    """
    Загрузка данных из переданного файла:
    Загрузка данных по указанным колонкам ds_col, y_col

    Поддерживаемые форматы: .xlsx, .xls, .csv

    Принимает:
        ds_col: str - Название колонки с датой
        temp_file -

    Возвращает:
        pd.DataFrame
            schema:
                    [('ds', pd.datetime64),
                    ('': float)]
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

    df = df.rename(columns={ds_col: 'ds'})
    return df


def _validation_forecasting_glocal(data, params, path):
    """
    Проверочное прогнозирование:
    Построение модели на основе найденных гиперпараметров

    Принимает:
        data: pd.DataFrame - данные
        params: dict - лучшая комбинация гиперпараметров
        path: str - директория сохранения результатов
    """
    forecast_result = pd.DataFrame()
    mae_df = pd.DataFrame()
    mape_df = pd.DataFrame()

    train_melt = data[:-params['n_forecasts']].melt(id_vars='ds',
                                                    var_name='ID',
                                                    value_name='y')
    test_melt = data[-params['n_forecasts']:]

    model = NeuralProphet(**params)
    model.add_country_holidays('RUS')

    _ = model.fit(train_melt)
    future = model.make_future_dataframe(
        train_melt, periods=params['n_forecasts'])
    forecast = model.predict(future)

    for col in forecast.ID.unique():
        forecast_result[col] = model.get_latest_forecast(forecast[forecast.ID == col])[
            'origin-0'][-params['n_forecasts']:].values
    forecast_result['ds'] = forecast.ds[-params['n_forecasts']:].values

    for col in forecast_result.columns.drop('ds'):
        mae_df[col] = mae_gl(test_melt[col].values,
                             forecast_result[col].values)
        mape_df[col] = mape_gl(test_melt[col].values,
                               forecast_result[col].values)

    mae_df['ds'] = forecast_result['ds'].values
    mape_df['ds'] = forecast_result['ds'].values

    mae_df.to_excel(path + '/mae_df.xlsx', index=False)
    mape_df.to_excel(path + '/mape_df.xlsx', index=False)

    for col in forecast_result.columns.drop('ds'):
        valid_img = validation_plot(test_melt[col].values,
                                    forecast_result[col].values,
                                    test_melt['ds'],
                                    col,
                                    params['n_forecasts'],
                                    mape_df[col].mean(),
                                    mae_df[col].mean(),
                                    path=None)
        valid_img.save(path + f"/{col}_valid_plot.png")


# pylint: disable=too-many-arguments
def pipeline_glocal(ds_col, steps, validation_steps, trials,
                    temp_file, date_border=None, sheet_name=0, years=10, use_save=True):
    """
    Пайплайн для автоматического прозирования с использованием NeuralProphet:
    1. _data_loader - Загрузка данных
    2. _hyperparams_tuning - Поиск наилучшей комбинации гиперпараметров
    3. _validation_forecasting - Прогнозирование для проверки
    5. _sequential_ensemble - Последовательное обучение ансамбля из n_ensemble моделей NeuralProphet
    9. exist_checker - Проверка наличия прогнозирования с такими же параметрами/файлом
    10. insert_row - Запись в БД параметров успешной итерации прогнозирования

    Принимает:
        ds_col: str - Название колонки с датой
        y_col: str - Название колонки, которую нужно спрогнозировать
        steps: int - Количество шагов прогнозирования
        validation_steps: int - Количество шагов прогнозирования на валидации
        trials: int - Количество итераций настройки гиперпараметров
        temp_file: Файл
    """
    filterwarnings('ignore')
    set_log_level("ERROR")

    if use_save == 'Да':
        # Проверка генерации с такими же параметрами
        exist_status, exist_dir, _id = exist_checker(ds_col,
                                                     '',
                                                     steps,
                                                     validation_steps,
                                                     trials,
                                                     temp_file.name.split(
                                                         '/')[-1],
                                                     1,
                                                     date_border,
                                                     sheet_name,
                                                     years)
        if exist_status:
            return _id, exist_dir, gr.File.update(value=exist_dir, visible=True)

    path = f"apps/forecasting_result/{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_glocal_{steps}_st/"

    Path(path).mkdir(parents=True, exist_ok=True)

    data = _data_loader_glocal(ds_col, temp_file, sheet_name)

    try:
        data['ds'] = pd.to_datetime(data.ds)
    except ValueError as e:
        raise gr.Error(f"Ошибка при преобразовании колонки {ds_col} в формат даты") from e

    if date_border:
        data = pd.concat([data[data.ds < pd.to_datetime(date_border)],
                          data[data.ds >= pd.to_datetime(date_border)].iloc[:steps, :]],
                         ignore_index=True)

    data = data[data.ds.dt.year >= datetime.datetime.now().year -
                years].reset_index(drop=True)

    best_params, _ = _hyperparams_tuning_glocal(
        data, validation_steps, path, trials)

    _validation_forecasting_glocal(data, best_params, path)

    best_params['n_forecasts'] = steps
    forecast = _sequential_ensemble_glocal(data, best_params, path)

    for col in forecast.columns.drop('ds'):
        forecasting_img = forecasting_plot(forecast[['ds', col]].rename(
            columns={'ds': 'Дата', col: 'Прогноз'}), col, steps, None)
        forecasting_img.save(path + f'/forecast_{col}.png')
        bins_img = forecasting_plot_bins(forecast[['ds', col]].rename(
            columns={'ds': 'Дата', col: 'Прогноз'}), None)
        bins_img.save(path + f'/forecast_bins_{col}.png')

    forecast.to_excel(path + 'forecast.xlsx', index=False)

    archive_path = shutil.make_archive(path[:-1], 'zip', path[:-1])

    # shutil.rmtree(path, ignore_errors=True)

    _id = insert_row(ds_col, '', steps, validation_steps, trials,
                     temp_file.name.split('/')[-1], 1, date_border, sheet_name, years, archive_path)

    return _id, archive_path, gr.File().update(archive_path)


def get_result_gl(_id, path=None):
    """
    Загрузка результатов с помощью id запуска прогнозирования / пути к директории
    """
    if path:
        try:
            return gr.File.update(value=path, visible=True)
        except FileNotFoundError as e:
            raise gr.Error(f'Путь не найден либо файлы повреждены при сохранении: {e}') from e

    if _id and not path:
        exist_status, path = result_getting(_id)
        if not exist_status:
            raise gr.Error('Результат не найден по этому id')

    return gr.File.update(value=path, visible=True)
