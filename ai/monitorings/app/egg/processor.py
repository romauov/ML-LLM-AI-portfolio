"""
Скрипт для обработки одного файла мониторинга яйца
"""
import pandas as pd

from app.common.processor import process_price
from app.egg.data import (column_mapping, drop_cols, egg_allowed_names)
from app.common.extractor import extract_date_from_file_name, get_file_name_by_path
from app.egg.extractor import extract_egg_category
from app.utils.logger import logger as log


def process_egg_file(file_path: str, skiprows: int = 3) -> pd.DataFrame:
    date_str = extract_date_from_file_name(file_path)
    file_name = get_file_name_by_path(file_path, include_parent_name=True)

    sheet_names_ = pd.ExcelFile(file_path).sheet_names
    sheet_names = []

    for name in sheet_names_:
        if name in egg_allowed_names:
            sheet_names.append(name)

    combined_data = None

    for sheet_name in sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows)

        if not df.columns.astype(str).str.contains('Округ', case=False).any():
            result = False
            for shift in [0, 1, -1, 2, -2, 3]:
                if not result:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows + shift)
                    if df.columns.astype(str).str.contains('Округ', case=False).any():
                        result = True
                        break
            if not result:
                log.error(f"Не удалось распарсить {file_path} - лист '{sheet_name}' в датафрейм")

        df = df.iloc[1:]
        df.columns = [col.capitalize() for col in df.columns]
        df.drop(columns=drop_cols, inplace=True, errors='ignore')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        if date_str:
            df["Дата"] = date_str

        if combined_data is None:
            combined_data = df
        else:
            combined_data = pd.concat([combined_data, df], ignore_index=True)

    processed_df = combined_data.copy()
    processed_df['Цена'] = processed_df['Цена'].replace('нет свободного объема', None)
    processed_df['Цена'] = processed_df['Цена'].apply(process_price)
    processed_df['category'] = 'Яйца'
    processed_df['Дата'] = pd.to_datetime(processed_df['Дата'], format="%d.%m.%Y")
    processed_df['week_number'] = processed_df['Дата'].dt.isocalendar().week
    processed_df['file_name'] = file_name
    processed_df['Категория'] = processed_df['Категория'].apply(extract_egg_category)
    processed_df.rename(columns=column_mapping, inplace=True)
    processed_df = processed_df.where(pd.notnull(processed_df), None)

    return processed_df
