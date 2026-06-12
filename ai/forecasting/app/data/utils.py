import json

import pandas as pd
import numpy as np

from app.database.db import get_macroeconomic_indicators, get_agro_indicators


def interpolate_for_each_category(df, category_col, target_cols):
    """
    Линейная интрполяция target_cols по каждому уникальному category_col.
    :param df: dataframe.
    :param category_col: Название колонки с категорией.
    :param target_cols: Список с названиями колонок для которых выполняется интерполяция.
    :return: dataframe.
    """
    for cat in df[category_col].unique().tolist():
        df_ = df[df[category_col] == cat]
        df.loc[df_.index, target_cols] = df_[target_cols].interpolate('linear', limit_direction='both').round(2)
    return df


def handle_outliers_by_sliding_window(df, target_col, category_col, window_size):
    """
    Замена выбросов на медианное значение скользящего окна.
    :param df: dataframe.
    :param target_col: Название колонки с ценой.
    :param window_size: Ширина окна.
    :param category_col: Название колонки с категорией.
    :return: dataframe с обработанными выбросами.
    """

    def is_outlier(x):
        """
        Функция определения выброса.
        :param x: значения ряда окна.
        :return: bool.
        """

        mean = np.median(x)
        std = np.std(x)
        mu = 3

        result = (x < mean - mu * std) + (x > mean + mu * std)
        return result.iloc[-1]

    result = []
    for id_ in df[category_col].unique().tolist():
        df_ = df[(df[category_col] == id_)].copy()
        df_['outlier'] = df_[target_col].rolling(window_size, center=False).apply(is_outlier)
        df_['sliding_window_mean'] = df_[target_col].rolling(window_size, center=False).median()

        # заменяем выбросы средним значением окна
        df_outlines = df_[df_['outlier'] == True]
        df_.loc[df_outlines.index, target_col] = df_outlines['sliding_window_mean'].values
        df_ = df_.drop(['outlier', 'sliding_window_mean'], axis=1)
        result.append(df_)

    df = pd.concat(result, axis=0)
    return df


def group_by_frequency(frequency, df, grouping_columns, date_col, target_col):
    """
    Группировка данных по неделям.
    :param frequency: Частота данных. For full specification of available frequencies
        <https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases>.
    :param target_col: Название колонки с целевым значением.
    :param date_col: Название колонки типа DateTime.
    :param df: dataframe.
    :param grouping_columns: List с названиями колонок по которым группируются данные.
    :return: dataframe.
    """
    df = df.groupby(
        by=[*grouping_columns, pd.Grouper(key=date_col, freq=frequency, label="left", closed="left")],
        dropna=False
    ).mean(target_col).reset_index()
    return df


def set_equal_date_frequency(df, date_from, date_to, category_col, date_col, freq='1d'):
    """
    Устанавливает одинаковую частоту даты в данных для каждого уникального значения category_col.
    :param date_col: Название колонки типа DateTime.
    :param date_to: Минимальная дата.
    :param date_from: Максимальная дата.
    :param df: dataframe с колонками ID и date.
    :param freq: Размер шага между данных. https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
    :param category_col: Название колонки с категорией.
    :return: dataframe.
    """
    date_range_df = pd.DataFrame(pd.date_range(start=date_from, end=date_to, freq=freq), columns=['date'])

    nd = len(date_range_df)
    nu = len(df[category_col].unique())

    df_expanded = pd.DataFrame({
        category_col: df[category_col].unique().tolist() * nd,
        date_col: np.repeat(date_range_df, nu)
    })
    df = df_expanded.merge(df, how='left')
    return df


def exponential_weighting(df, lag, category_col, target_col):
    """
    Экспоненциальное взвешивание target_col по каждому уникальному category_col.
    :param target_col: Название колонки с целевым значением.
    :param df: dataframe.
    :param lag: int величина лага.
    :param category_col: Название колонки с категорией.
    :return: dataframe.
    """
    df_ = df.copy()
    for cat in df_[category_col].unique().tolist():
        vals = df_[df_[category_col] == cat][target_col].ewm(lag).mean()
        df.loc[vals.index, target_col] = vals.values
    return df


def get_time_series_frequency(df, date_column_name, category_col=None):
    """
    Определение дискретности временного ряда.
    :param df: dataframe.
    :param date_column_name: название колонки с датой.
        :param category_col: Название колонки с категорией.
    :return: str: алиас дискретности 'W', 'M', 'MS'
    """
    # if have multiple unique ID, got first for determine frequency
    if category_col:
        category = df[category_col].unique().tolist()[0]
        df = df[df[category_col] == category]
    freq = pd.infer_freq(df[date_column_name])
    if not freq:
        raise ValueError('Unable to determine the frequency of timestamps in the data')
    return freq


def get_seasonal_periods_by_date_frequency(date_frequency):
    """
    Получение длины сезона по дискретности данных.
    :param date_frequency: дискретность данных.
    :return: int длина сезона.
    """
    if date_frequency[0] == 'D':
        return 356
    elif date_frequency[0] == 'W':
        return 52
    elif date_frequency[0] == 'M':
        return 12
    elif date_frequency[0] == 'Q':
        return 4


def add_global_indicators(df, cfg):
    """
    Добавление макроэкономических и аграрных показателей в датафрейм.
    :param df: dataframe.
    :return: dataframe.
    """
    df = df.copy()

    def merge(first, second):
        return pd.merge(
            first,
            second,
            left_on=[first['ds'].dt.year, first['ds'].dt.month],
            right_on=[second['ds'].dt.year, second['ds'].dt.month],
            how='left',
            suffixes=('', '_y'),
        ).drop(['key_0', 'key_1', 'ds_y'], axis=1)

    df_macroeconomic = get_macroeconomic_indicators(cfg=cfg)
    # приводим к единой ежемесячной дискретности показателей
    df_macroeconomic = df_macroeconomic.groupby(pd.Grouper(key='ds', freq='MS')).mean().reset_index()
    df = merge(df, df_macroeconomic)

    df_agro = get_agro_indicators(cfg=cfg)
    # приводим к единой ежемесячной дискретности показателей
    df_agro = df_agro.groupby(pd.Grouper(key='ds', freq='MS')).mean().reset_index()
    df = merge(df, df_agro)

    interpolate_columns = list(set(df.columns) - {'ID', 'ds', 'y'})
    df = interpolate_for_each_category(df, category_col='ID', target_cols=interpolate_columns)

    # удаляем константные макроэкономические показатели
    other_cols = df.loc[:, ~df.columns.isin(['ds', 'y', 'ID'])].columns
    df = df.drop(df[other_cols].columns[df[other_cols].nunique() <= 1], axis=1)
    return df


def get_cross_validation_split_ids(df, k_folds, category_col):
    """
    Генератор. Возвращает фолды с train_ids и test_ids для каждого уникального category_col.
    :param df: dataframe с временными рядами.
    :param k_folds: количество фолдов разбиения данных.
    :param category_col: название колонки с уникальными названиями временных рядов.
    :return: List[train_id], List[test_id], List[int] длина тестовых данных.
    """
    train_ids = []
    test_ids = []

    for cat in df[category_col].unique().tolist():
        df_ = df[df[category_col] == cat]

        # length of the test set is 1/3 from dataframe length
        test_length = int(len(df_) / 3)

        train_id = df_[:-test_length].index
        test_id = np.array_split(df_[-test_length:].index, k_folds)

        train_ids.extend(train_id)
        test_ids.append(test_id)

    # grouping test id from each fold by category
    test_ids_grouped_by_category = [np.hstack(sub_arrays) for sub_arrays in zip(*test_ids)]

    for fold_idx in range(k_folds):
        test_data_length = len(test_ids[0][fold_idx])
        if fold_idx > 0:
            # adding to training set id from the previous test fold
            train_ids.extend(test_ids_grouped_by_category[fold_idx - 1])

        yield train_ids, test_ids_grouped_by_category[fold_idx], test_data_length


def dataframe_columns_to_json_sting(df, columns):
    return df[columns].apply(
        lambda x: json.dumps(
            {k: v for k, v in x.to_dict().items() if v is not None},
            ensure_ascii=False
        )
        .replace('\\"', '"')
        .replace('"[', '[')
        .replace(']"', ']'),
        axis=1
    )
