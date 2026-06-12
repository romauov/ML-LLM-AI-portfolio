"""
Утилиты для работы с pandas DataFrame

@authors: Nikolay Zhabchikov
"""
import json
from typing import List, Tuple

import numpy as np
import pandas as pd
from pandas import Index


def pandas_label_encode(
        df: pd.DataFrame,
        column_name: str,
        threshold: int = 2,
        empty_name: str = 'empty',
        rare_name: str = 'rare'
) -> Tuple[np.ndarray, Index]:
    """
    Кодирует категориальные признаки в числовые метки.

    Обрабатывает пропущенные значения, объединяет редкие категории
    и выполняет факторизацию оставшихся значений.

    Args:
        df: DataFrame с данными для кодирования.
        column_name: Название колонки для кодирования.
        threshold: Минимальное количество вхождений категории, чтобы не считаться редкой.
                   Категории с меньшим количеством вхождений заменяются на rare_name.
                   По умолчанию 2.
        empty_name: Значение, которым заполняются пропуски в колонке. По умолчанию 'empty'.
        rare_name: Значение, которым заменяются редкие категории. По умолчанию 'rare'.

    Returns:
        Кортеж из двух элементов:
            - encoded_labels: ndarray с закодированными метками (целые числа от 0 до n-1).
            - uniques: Index с уникальными значениями категорий после обработки.
    """
    if column_name not in df.columns:
        raise KeyError(f"Колонка '{column_name}' не найдена в DataFrame")

    if threshold < 0:
        raise ValueError(f"threshold должен быть >= 0, получено {threshold}")

    # Работаем с копией только для модификации колонки
    df_copy = df.copy()
    df_copy[column_name] = df_copy[column_name].fillna(empty_name)

    value_counts = df_copy[column_name].value_counts()
    rare_categories = value_counts[value_counts < threshold].index.tolist()

    if rare_categories:
        df_copy[column_name] = df_copy[column_name].replace(rare_categories, rare_name)

    encoded_labels, uniques = pd.factorize(df_copy[column_name])

    return encoded_labels, uniques


def dataframe_columns_to_json_string(
        df: pd.DataFrame,
        columns: List[str]
) -> pd.Series:
    """
    Преобразует указанные колонки DataFrame в JSON-строку.

    Каждая строка выбранных колонок преобразуется в JSON-объект,
    из которого исключаются значения None.

    Args:
        df: DataFrame с данными для преобразования.
        columns: Список названий колонок для преобразования в JSON.

    Returns:
        Series с JSON-строками, по одной на каждую строку DataFrame.
    """
    if not columns:
        raise ValueError("Список columns не должен быть пустым")

    missing_columns = [col for col in columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Колонки не найдены в DataFrame: {missing_columns}")

    return df[columns].apply(
        lambda x: json.dumps(
            {k: v for k, v in x.items() if v is not None},
            ensure_ascii=False
        ),
        axis=1
    )
