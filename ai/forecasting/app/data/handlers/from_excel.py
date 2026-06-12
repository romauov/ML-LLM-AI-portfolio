from datetime import datetime
import pandas as pd

from app.common.logger import logger as log
from app.data.utils import get_time_series_frequency, get_seasonal_periods_by_date_frequency, \
    handle_outliers_by_sliding_window


def get_data_from_exel_file(file_path, cfg, sheet_name, date_column_name, forecast_column_name,
                            history_years_limit=None):
    """
    Загрузка данных с excel файла.
    :param file_path: путь к excel файлу.
    :param sheet_name: название листа с временным рядом.
    :param date_column_name: название колонки с датой.
    :param forecast_column_name: название колонки с прогнозируемым временным рядом.
    :param history_years_limit: количество лет, которые надо учитывать в временном ряде.
    :return: dataframe.
    """
    log.info('loading data from excel file')
    df = _transform_excel_to_model_format(file_path, sheet_name, date_column_name, forecast_column_name, cfg,
                                          history_years_limit)

    date_freq = get_time_series_frequency(df, 'ds')
    cfg.exponential_smoothing.model.freq = date_freq
    cfg.neuralprophet.train.freq = date_freq
    cfg.prophet.train.freq = date_freq
    cfg.exponential_smoothing.model.seasonal_periods = get_seasonal_periods_by_date_frequency(date_freq)
    log.info('end load and handle data')
    return df


def _transform_excel_to_model_format(file_path, sheet_name, date_column_name, forecast_column_name, cfg,
                                     history_years_limit=None):
    df = pd.read_excel(file_path, sheet_name)
    df = df.rename(columns={date_column_name: 'ds', forecast_column_name: 'y'})

    if history_years_limit:
        date_limit = df['ds'].max() - pd.DateOffset(years=history_years_limit)
        df = df[df['ds'] >= date_limit]

    df['ID'] = forecast_column_name
    df = df[['ds', 'y', 'ID']]

    df = handle_outliers_by_sliding_window(
        df=df,
        target_col='y',
        category_col='ID',
        window_size=cfg.outliers_sliding_window_size
    )
    return df
