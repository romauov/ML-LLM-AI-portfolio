import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Union, Tuple, Any, Optional, List

from app.data.handlers.main import get_data_by_config
from app.database.db import get_predictions_by_date, save_grafana_dashboard_mape_metrics, \
    get_forecasting_dates_with_enough_data_for_metrics
from app.common.evaluation_metrics import mean_absolute_percentage_error
from config.configs import Config


def _get_from_to_dates_by_forecasting_date(
        forecasting_date: Union[str, datetime],
        freq: str,
        n_forecasts: int,
        dates_format: str = '%Y-%m-%d'
) -> Tuple[str, str]:
    """
    Вычисляет начальную и конечную даты на основе даты прогнозирования, частоты и количества прогнозов.

    :param forecasting_date: Дата прогнозирования. Может быть строкой в формате '%Y-%m-%d %H:%M:%S' или объектом datetime.
    :param freq: Частота прогнозирования ('W' для недельного, 'M' для месячного).
    :param n_forecasts: Количество прогнозов.
    :param dates_format: Формат вывода дат. По умолчанию '%Y-%m-%d'.
    :return: Кортеж из двух строк: начальная и конечная даты в заданном формате.
    """
    if isinstance(forecasting_date, str):
        date_from = datetime.strptime(forecasting_date, '%Y-%m-%d %H:%M:%S')
    elif isinstance(forecasting_date, datetime):
        date_from = forecasting_date
    else:
        raise KeyError(f'unsupported forecasting_date type {type(forecasting_date)}')

    if freq.startswith('W'):
        shift = timedelta(weeks=n_forecasts)
        date_to = date_from + shift
    elif freq.startswith('M'):
        date_to = date_from + relativedelta(months=n_forecasts)
    else:
        raise KeyError(f'unsupported freq type {freq}')

    return date_from.strftime(dates_format), date_to.strftime(dates_format)


def _get_filtered_history_data(cfg: Any, date_from: str, date_to: str) -> pd.DataFrame:
    """
    Получает и фильтрует исторические данные.

    :param cfg: Объект конфигурации.
    :param date_from: Начальная дата периода для получения исторических данных.
    :param date_to: Конечная дата периода для получения исторических данных.
    :return: Отфильтрованный DataFrame с историческими данными.
    """
    # сбор данных из базы данных на период прогнозирования
    df_history = get_data_by_config(cfg=cfg, date_from=date_from, date_to=date_to, for_dashboard=True)

    # удаление категорий, где данных меньше, чем половина прогнозируемых точек, чтобы сильно не смещать статистику
    cats = df_history['ID'].value_counts()
    df_history = df_history[~df_history['ID'].isin(cats[cats < cfg.n_forecasts / 2].index.tolist())]

    return df_history


def _merge_history_and_predictions(df_history: pd.DataFrame, df_preds: pd.DataFrame) -> pd.DataFrame:
    """
    Объединяет исторические и прогнозные данные по датам и ID.

    :param df_history: DataFrame с историческими данными.
    :param df_preds: DataFrame с прогнозными данными.
    :return: Объединенный DataFrame.
    """
    return pd.merge(left=df_history, right=df_preds, how='inner', on=['ds', 'ID'])


def _get_processed_prediction_data(forecasting_date: str) -> pd.DataFrame:
    """
    Получает и предварительно обрабатывает прогнозные данные.

    :param forecasting_date: Дата, для которой были сделаны прогнозы.
    :return: Обработанный DataFrame с прогнозными данными.
    """
    df_preds = get_predictions_by_date(date=forecasting_date).reset_index(drop=True)
    df_preds = df_preds.rename(columns={'date': 'ds', 'time_series_id': 'ID'})
    df_preds['ds'] = pd.to_datetime(df_preds['ds'])

    return df_preds


def _calculate_and_group_mape(df: pd.DataFrame) -> pd.DataFrame:
    """
    Вычисляет MAPE и группирует результаты по ID и модели.

    :param df: DataFrame с объединенными историческими и прогнозными данными.
    :return: DataFrame с колонками 'ID', 'model', 'mape', содержащий средние значения MAPE для каждой модели и категории.
    """
    df['mape'] = df.apply(lambda x: mean_absolute_percentage_error(y_true=x.y, y_pred=x.price), axis=1)
    df = df[['ID', 'model', 'mape']].groupby(['ID', 'model']).mean().reset_index()

    return df


def _calculate_predictions_mape(cfg: Config, date_from: str, date_to: str, forecasting_date: str) -> pd.DataFrame:
    """
    Вычисляет среднюю абсолютную процентную ошибку (MAPE) для прогнозов.

    :param cfg: Объект конфигурации.
    :param date_from: Начальная дата периода для получения исторических данных.
    :param date_to: Конечная дата периода для получения исторических данных.
    :param forecasting_date: Дата, для которой были сделаны прогнозы.
    :return: DataFrame с колонками 'ID', 'model', 'mape', содержащий средние значения MAPE для каждой модели и категории.
    """
    # получение и фильтрация исторических данных
    df_history = _get_filtered_history_data(cfg, date_from, date_to)

    # получение и предварительная обработка прогнозных данных
    df_preds = _get_processed_prediction_data(forecasting_date)

    # объединение по категориям и датам
    df = _merge_history_and_predictions(df_history, df_preds)

    # вычисление MAPE и группировка результатов
    df = _calculate_and_group_mape(df)

    return df


def update_dashboard_for_accumulated_historical_data(
        cfg: Config,
        forecasting_dates: Optional[List[str]] = None
) -> None:
    """
    Обновляет данные для дашборда Grafana на основе накопленных исторических данных.

    :param cfg: Объект конфигурации.
    :param forecasting_dates: Список дат прогнозирования. Если None, то будут получены даты из базы данных.
    :return: None
    """
    if not forecasting_dates:
        forecasting_dates = get_forecasting_dates_with_enough_data_for_metrics(
            freq=cfg.freq, n_forecasts=cfg.n_forecasts
        )

    for forecasting_date in forecasting_dates:
        date_from, date_to = _get_from_to_dates_by_forecasting_date(
            forecasting_date, freq=cfg.freq, n_forecasts=cfg.n_forecasts
        )
        df = _calculate_predictions_mape(cfg, date_from=date_from, date_to=date_to, forecasting_date=forecasting_date)
        df['date'] = forecasting_date
        save_grafana_dashboard_mape_metrics(df)
