"""
Функции для проверки формата данных необходимого для моделей.

@author Nikolay Zhabchikov
"""

import os
import pandas as pd
from datetime import datetime
from contextlib import suppress
from fastapi import HTTPException, status

from app.data.utils import get_seasonal_periods_by_date_frequency, get_cross_validation_split_ids
from app.common.logger import logger as log


def handle_assert_as_http_error(status_code):
    """
    Параметризированный декоратор, обрабатывает AssertionError, как HTTPException
    :param status_code: http статус код ошибки.
    :return:
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except AssertionError as e:
                raise HTTPException(status_code=status_code, detail=str(e))

        return wrapper

    return decorator


class DataChecker:
    def __init__(self, cfg):
        self.cfg = cfg

    @staticmethod
    def excel_has_sheet(path, sheet_name):
        """
        Проверка наличия листа в excel файле.
        :param path: путь до excel файла.
        :param sheet_name: название листа.
        :return: dataframe.
        """
        file = pd.ExcelFile(path)
        assert sheet_name in file.sheet_names, f'{sheet_name} not found in excel file sheets'
        return pd.read_excel(file, sheet_name=sheet_name)

    @staticmethod
    def df_has_col(df, col):
        """
        Проверка наличия колонки в dataframe.
        :param df: dataframe.
        :param col: название колонки.
        :return:
        """
        assert col in df.columns, f'{col} not found in dataframe columns'

    @staticmethod
    def df_date_frequency(df, date_name):
        """
        Проверка дискретности временных точек данных и равномерности распределения.
        :param df: dataframe.
        :param date_name: название колонки с датой.
        :return: алиас дискретности временных точек. 'D', 'W', 'ME'
        """
        freq = pd.infer_freq(df[date_name])
        assert freq is not None, 'Unable to determine the frequency of timestamps in the data'
        return freq

    @staticmethod
    def df_min_length(df, season_length):
        """
        Проверка длинный временного ряда.
        :param df: dataframe.
        :param season_length: длина одного сезона.
        :return:
        """
        assert len(df) >= season_length * 3, f'dataset length is less than 3 seasons. {len(df)} < {season_length * 3}'

    @staticmethod
    def df_has_no_nan_values(df):
        assert df.isna().sum().sum() == 0, 'daset has NaN values'

    def minimum_unique_points(self, df, category_col, target_col, drop=False):
        """
        Проверка наличия минимального количества уникальных значений target_col по каждому уникальному category_col.
        :param df: dataframe.
        :param category_col: Название колонки с категорией.
        :param target_col: Название колонки с целевым значением.
        :param drop: Удалить категории с уникальными значениям менее чем min_unique_points.
        :return:
        """
        df_ = df.copy().reset_index(drop=True)
        ids = None

        for train_ids, _, _ in get_cross_validation_split_ids(
                df_,
                k_folds=self.cfg.cross_validation_k_folds,
                category_col=category_col
        ):
            df_to_check = df_.loc[train_ids]
            ids = df_to_check.groupby([category_col]).filter(
                lambda x: x[target_col].nunique() < self.cfg.min_unique_points
            )[category_col].unique().tolist()

            break

        if ids:
            if drop:
                log.info(f'dropped categories because they have less than {self.cfg.min_unique_points} '
                         f'unique price at data points at dataset:{ids}')
                df = df[~df[category_col].isin(ids)]
                return df
            else:
                assert ids is None, (f'dataset has categories that have less than {self.cfg.min_unique_points} '
                                     f'unique price at data points. IDs: {ids}')
        return df

    @handle_assert_as_http_error(status_code=status.HTTP_400_BAD_REQUEST)
    def check_data_from_excel(self, file_path, sheet_name, date_name, series_name, history_years_limit=None):
        """
        Pipline проверки данных из excel файла.
        :param file_path: путь до excel файла.
        :param sheet_name: название листа excel файла.
        :param date_name: название колонки с датой.
        :param series_name: название прогнозируемой колонки.
        :param history_years_limit: лимит исторических данных в годах.
        :return:
        """
        try:
            df = self.excel_has_sheet(file_path, sheet_name)
            self.df_has_col(df, date_name)
            self.df_has_col(df, series_name)
            self.df_has_no_nan_values(df)
            df[date_name] = pd.to_datetime(df[date_name])

            if history_years_limit:
                date_limit = df[date_name].max() - pd.DateOffset(years=history_years_limit)
                df = df[df[date_name] >= date_limit]

            freq = self.df_date_frequency(df, date_name)
            season_length = get_seasonal_periods_by_date_frequency(freq)
            self.df_min_length(df, season_length)

            # проверка минимальной длины по длине сезона из конфига
            self.df_min_length(df, self.cfg.exponential_smoothing.model.seasonal_periods)

        except AssertionError:
            with suppress(FileNotFoundError):
                os.remove(file_path)
            raise

    def check_data_from_database(self, df, category_col):
        """
        Pipline проверки данных из базы данных.
        :param df: dataframe.
        :param category_col: название колонки с уникальной категорией временного ряда.
        :return:
        """
        category = df[category_col].unique().tolist()[0]
        df = df[df[category_col] == category]

        freq = self.df_date_frequency(df, 'ds')
        season_length = get_seasonal_periods_by_date_frequency(freq)
        self.df_min_length(df, season_length)
