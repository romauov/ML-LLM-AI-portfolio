"""
Скрипт для обработки одного файла мониторинга

@author Sergei Romanov
"""
import json
import os
import re

import pandas as pd

from app.common.extractor import get_file_name_by_path
from app.common.processor import process_price
from app.meat.processor.data_processor import process_dataframe_cols
from app.meat.utils.data import column_mapping, drop_cols, meat_type_map, old_column_mapping, csv_file_categories
from app.utils.data import okrug_map
from app.utils.logger import logger as log


def process_from_excel(file_path: str, skiprows: int = 8) -> pd.DataFrame:
    file_name = get_file_name_by_path(file_path, include_parent_name=False)

    combined_data = None
    for sheet_name, _ in meat_type_map.items():
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows)
        df = df.iloc[1:]
        df.columns = [col.capitalize() for col in df.columns]
        df.drop(columns=drop_cols, inplace=True, errors='ignore')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.rename(columns=old_column_mapping, inplace=True)

        match = re.search(r"(\d{2}\.\d{2}\.\d{4})", file_path)
        if match:
            date_str = match.group(1)
            df["Дата"] = date_str

        else:
            log.error(f"Could not extract date from {file_path}")

        okrug_code_match = re.match(r'^[a-zA-Z]+', os.path.basename(file_path))
        if okrug_code_match:
            okrug_code = okrug_code_match.group(0).lower()
            if okrug_code in okrug_map:
                df["federal_okrug"] = okrug_map[okrug_code]
            else:
                log.error(f"Unknown federal okrug code: {okrug_code} in file {file_path}")

        else:
            log.error(f"Could not extract federal okrug code from {file_path}")

        if combined_data is None:
            combined_data = df
        else:
            combined_data = pd.concat([combined_data, df], ignore_index=True)

    processed_df = process_dataframe_cols(combined_data)
    processed_df['category'] = 'Мясо и мясопродукты'
    processed_df['Дата'] = pd.to_datetime(processed_df['Дата'])
    processed_df['week_number'] = processed_df['Дата'].dt.isocalendar().week
    processed_df['file_name'] = file_name
    processed_df.rename(columns=column_mapping, inplace=True)
    processed_df = processed_df.where(pd.notnull(processed_df), None)
    return processed_df


def process_from_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path, sep=';')
    file_name = get_file_name_by_path(file_path, include_parent_name=False)

    df['date'] = pd.to_datetime(df['date'])
    df['week_number'] = df['date'].dt.isocalendar().week
    df['file_name'] = file_name
    df['price'] = df['price'].apply(process_price)
    df['country'] = 'Россия'
    df['product_details'] = df['product_details'].apply(
        lambda x: json.dumps(x.split(','), ensure_ascii=False) if isinstance(x, str) else x
    )
    df = df[csv_file_categories]
    return df
