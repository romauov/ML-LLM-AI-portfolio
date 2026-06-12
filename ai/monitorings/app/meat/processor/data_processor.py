"""
Скрипты для обработки данных сырых мониторингов

@author Sergei Romanov
"""
import json
import re

import pandas as pd

from app.common.processor import process_price
from app.meat.utils.data import product_details_patterns


def extract_sort(description):
    """
    Извлекает сорт (например, "1 сорт") из столбца 'Описание'.

    Args:
        description (str): Строка описания.

    Returns:
        str or None: Извлеченный сорт или None, если не найден.
    """
    match = re.search(r'(\d)\s*[с|сорт|кат]*', description)
    if match:
        return f"{match.group(1)} сорт"
    return None


def extract_cert(description):
    """
    Извлекает типы сертификации (например, "гост", "ту", "халяль") из столбца 'Описание'.

    Args:
        description (str): Строка описания.

    Returns:
        str or None: Извлеченный тип сертификации или None, если не найден.
    """

    match = re.search(r'\b(гост|ту|халяль)\b', description, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def extract_frozen_chilled(value, need_sea_frozen=False):
    """
    Обрабатывает столбец 'Зам./ Охл.', стандартизируя значения в 'зам' или 'охл'.

    Args:
        value (str): Значение из столбца 'Зам./ Охл.'.
        need_sea_frozen (bool): Если true, то добавляется обработка 'с/м' заморозки

    Returns:
        str: Стандартизированное значение ('зам', 'охл' или исходное значение, если не найдено совпадение).
    """
    value = str(value).lower().strip()
    if need_sea_frozen:
        if 'с/м' in value or 'с\\м' in value:
            return 'с/м'
    if 'зам' in value or 'охл./зам' in value:
        return 'зам'
    elif 'охл' in value:
        return 'охл'
    else:
        return value

def extract_product_details(description):
    """
    Извлекает детали продукта из столбца 'Описание' используя регулярные выражения.
    Args:
        description (str): Строка описания.
    Returns:
        list: Список найденных деталей продукта.
    """
    if not description or pd.isna(description):
        return []

    description = str(description).lower()
    found_details = []

    for detail_name, pattern in product_details_patterns.items():
        if re.search(pattern, description, re.IGNORECASE):
            found_details.append(detail_name)

    return found_details

def process_dataframe_cols(df):
    """
    Обрабатывает DataFrame, преобразуя 'Цена' в число с плавающей запятой, 'Дата' в datetime,
    обрабатывая 'Зам./ Охл.', и сортируя DataFrame.

    Args:
        df (pd.DataFrame): DataFrame для обработки.

    Returns:
        pd.DataFrame: Обработанный DataFrame.
    """
    df = df.copy()
    df = df.astype({'Описание': str, 'Наименование': str})
    df['Наименование'] = df['Наименование'].str.capitalize()
    df.dropna(subset=['Описание'], inplace=True)
    df = df[df['Описание'].str.strip() != '']
    df['Цена'] = df['Цена'].apply(process_price)
    if 'Зам./ Охл.' in df.columns:
        df['Зам./ Охл.'] = df['Зам./ Охл.'].apply(extract_frozen_chilled)

    df["Дата"] = pd.to_datetime(df["Дата"], format="%d.%m.%Y", errors="coerce")
    df = df.sort_values("Дата")
    df['Сорт/Категория'] = df['Описание'].apply(extract_sort)
    df['Сертификация'] = df['Описание'].apply(extract_cert)

    # уникальные значения из файла мониторинга
    unique_descriptions = df['Описание'].unique()
    description_to_details = {}
    for description in unique_descriptions:
        details = extract_product_details(description)
        if details:
            description_to_details[description] = details
        else:
            description_to_details[description] = None

    # извлечение product_details
    df['Детали продукта'] = df['Описание'].map(description_to_details)

    # Сериализация в строку для БД
    if 'Детали продукта' in df.columns:
        df['Детали продукта'] = df['Детали продукта'].apply(
            lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else x)

    return df
