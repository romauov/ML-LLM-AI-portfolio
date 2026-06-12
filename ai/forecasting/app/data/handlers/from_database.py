"""
Функции по обработке данных.

@author Nikolay Zhabchikov
"""
import json

import pandas as pd
import numpy as np

from app.common.constants import MEAT_AND_MEAT_PRODUCTS, FISH_AND_SEAFOOD, ALL_FEDERAL_OKRUG
from app.data.checker import DataChecker
from app.data.utils import group_by_frequency, handle_outliers_by_sliding_window, set_equal_date_frequency, \
    interpolate_for_each_category, dataframe_columns_to_json_sting
from app.database.utils import product_config_to_sql_conditions
from app.database.db import get_meat_data, get_seafood_data, ProductsType
from app.common.logger import logger as log


def get_data_from_database(date_from, date_to, cfg, for_dashboard=False):
    """
    Загрузка данных из мониторингов.
    :param cfg: конфиг.
    :param date_from: дата начала выборки.
    :param date_to: дата конца выборки.
    :return: dataframe.
    """
    log.info(f'loading data from database, from {date_from} to {date_to}')

    seafood_df = _get_handled_seafood_data(ProductsType.seafood, date_from=date_from, date_to=date_to, cfg=cfg,
                                           for_dashboard=for_dashboard)
    caviar_df = _get_handled_seafood_data(ProductsType.caviar, date_from=date_from, date_to=date_to, cfg=cfg,
                                          for_dashboard=for_dashboard)
    fish_df = _get_handled_seafood_data(ProductsType.fish, date_from=date_from, date_to=date_to, cfg=cfg,
                                        for_dashboard=for_dashboard)
    shrimp_df = _get_handled_seafood_data(ProductsType.shrimp, date_from=date_from, date_to=date_to, cfg=cfg,
                                          for_dashboard=for_dashboard)
    semiprocessed_df = _get_handled_seafood_data(ProductsType.semiprocessed, date_from=date_from, date_to=date_to,
                                                 cfg=cfg, for_dashboard=for_dashboard)
    meat_df = _get_handled_meat_data(date_from=date_from, date_to=date_to, cfg=cfg, for_dashboard=for_dashboard)

    df = pd.concat((meat_df, seafood_df, caviar_df, fish_df, shrimp_df, semiprocessed_df), axis=0)
    df = df.reset_index(drop=True)

    log.info('end load and handle data')
    return df


def _get_handled_seafood_data(products_type: ProductsType, date_from, date_to, cfg, for_dashboard):
    """
    Получение рыбного датасета, подготовленного для моделей предсказания.
    :param products_type: Тип продукта [Морепродукты, Икра, Рыба, Креветки, Полуфабрикаты].
    :param date_from: дата начала выборки.
    :param date_to: дата конца выборки.
    :param cfg: конфиг.
    :return: dataframe.
    """
    match products_type:
        case ProductsType.seafood:
            products_cfg = cfg.seafood_products
        case ProductsType.caviar:
            products_cfg = cfg.caviar_products
        case ProductsType.fish:
            products_cfg = cfg.fish_products
        case ProductsType.shrimp:
            products_cfg = cfg.shrimp_products
        case ProductsType.semiprocessed:
            products_cfg = cfg.semiprocessed_products
        case _:
            raise KeyError('Unknown ProductsType')

    if not products_cfg:
        return pd.DataFrame()

    sql_conditions = product_config_to_sql_conditions(products_cfg)
    dfs = []
    for condition, product_cfg in zip(sql_conditions, products_cfg):
        df = get_seafood_data(
            products_type=products_type,
            sql_condition=condition,
            date_from=date_from,
            date_to=date_to
        )
        df = _handle_dataframe(df, product_cfg)
        dfs.append(df)

    df = pd.concat(dfs, axis=0) if len(dfs) > 1 else dfs[0]
    df = df.reset_index(drop=True)
    df['category'] = FISH_AND_SEAFOOD
    if for_dashboard:
        df = _transform_raw_to_dashboard_format(df, cfg)
    else:
        df = _transform_raw_to_model_format(df, date_from, date_to, cfg=cfg)
    return df


def _handle_dataframe(df, product_cfg):
    """
    Обработка датафрема полученного из базы данных.
    Подготоваливает данные для группировки путем удаления лишних столбцов и дополнительных значений в списках,
    которых нет в конфиге.
    :param df: dataframe.
    :param product_cfg: конфиг.
    :return: dataframe.
    """
    product_cfg_dict = product_cfg.dict()
    keys = product_cfg_dict.keys()
    static_cols = ['product', 'date', 'price', 'federal_okrug']

    for key, value in product_cfg:
        if isinstance(value, list) and key in df.columns:
            handled_value = []
            for item in value:
                if isinstance(item, str):
                    item = item.replace('%', '')
                handled_value.append(item)

            df[key] = json.dumps(handled_value, ensure_ascii=False)

    for col in df.columns:
        if (col not in keys and col not in static_cols) or (col in keys and product_cfg_dict[col] is None):
            df = df.drop(col, axis=1)

    return df


def _get_handled_meat_data(date_from, date_to, cfg, for_dashboard):
    """
    Получение мясного датасета, подготовленного для моделей предсказания.
    :param date_from: дата начала выборки.
    :param date_to: дата конца выборки.
    :param cfg: конфиг.
    :return: dataframe.
    """

    sql_conditions = product_config_to_sql_conditions(config=cfg.meat_products)
    dfs = []
    for i, (condition, product_cfg) in enumerate(zip(sql_conditions, cfg.meat_products)):
        df = get_meat_data(
            sql_condition=condition,
            date_from=date_from,
            date_to=date_to
        )
        df = _handle_dataframe(df, product_cfg)
        dfs.append(df)

    df = pd.concat(dfs, axis=0) if len(dfs) > 1 else dfs[0]
    df = df.reset_index(drop=True)
    df['category'] = MEAT_AND_MEAT_PRODUCTS
    if for_dashboard:
        df = _transform_raw_to_dashboard_format(df, cfg)
    else:
        df = _transform_raw_to_model_format(df, date_from, date_to, cfg=cfg)
    return df


def _transform_raw_to_model_format(df, date_from, date_to, cfg):
    """
    Обработка сырого датафрейма скачанного из базы данных в формат подходящий для моделей.
    :param df: dataframe.
    :param date_from: дата начала выборки.
    :param date_to: дата конца выборки.
    :param cfg: конфиг.
    :return: dataframe.
    """
    df.sort_values('date', ascending=True, inplace=True)

    # grouping on week by federal_okrug
    grouping_columns = df.columns[~df.columns.isin(['date', 'price'])]
    grouping_columns_without_okrug = [item for item in grouping_columns if item != 'federal_okrug']
    df_by_okrug = group_by_frequency(cfg.freq, df, grouping_columns, 'date', 'price')
    df_all_okrug = group_by_frequency(cfg.freq, df, grouping_columns_without_okrug, 'date', 'price')
    df_all_okrug['federal_okrug'] = ALL_FEDERAL_OKRUG
    df = pd.concat((df_by_okrug, df_all_okrug), axis=0)

    df = df.replace({np.nan: None})
    df['ID'] = dataframe_columns_to_json_sting(df, grouping_columns)
    df.drop(grouping_columns, axis=1, inplace=True)

    df = handle_outliers_by_sliding_window(
        df=df,
        target_col='price',
        category_col='ID',
        window_size=cfg.outliers_sliding_window_size
    )
    df = set_equal_date_frequency(df, date_from, date_to, freq=cfg.freq, category_col='ID', date_col='date')
    df = interpolate_for_each_category(df, category_col='ID', target_cols=['price'])
    df = DataChecker(cfg).minimum_unique_points(
        df,
        category_col='ID',
        target_col='price',
        drop=True
    )

    df = df.rename(columns={'date': 'ds', 'price': 'y'})
    return df


def _transform_raw_to_dashboard_format(df, cfg):
    df.sort_values('date', ascending=True, inplace=True)

    # grouping on week by federal_okrug
    grouping_columns = df.columns[~df.columns.isin(['date', 'price'])]
    grouping_columns_without_okrug = [item for item in grouping_columns if item != 'federal_okrug']
    df_by_okrug = group_by_frequency(cfg.freq, df, grouping_columns, 'date', 'price')
    df_all_okrug = group_by_frequency(cfg.freq, df, grouping_columns_without_okrug, 'date', 'price')
    df_all_okrug['federal_okrug'] = ALL_FEDERAL_OKRUG
    df = pd.concat((df_by_okrug, df_all_okrug), axis=0)

    df = df.replace({np.nan: None})
    df['ID'] = dataframe_columns_to_json_sting(df, grouping_columns)
    df.drop(grouping_columns, axis=1, inplace=True)

    df = df.rename(columns={'date': 'ds', 'price': 'y'})
    return df
