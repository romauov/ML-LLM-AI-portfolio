"""
Скрипт для обработки одного файла мониторинга фруктов
"""
import os
import pandas as pd

from app.common.processor import process_price
from app.fruit.data import column_mapping, drop_cols, fruit_allowed_names, old_column_mapping, subfolder_to_okrug
from app.common.extractor import extract_date_from_file_name, extract_federal_okrug_from_file_name, \
    get_file_name_by_path
from app.utils.logger import logger as log


def process_fruit_file(file_path: str, skiprows: int = 0) -> pd.DataFrame:
    date_str = extract_date_from_file_name(file_path)
    file_name = get_file_name_by_path(file_path, include_parent_name=True)

    federal_okrug = extract_federal_okrug_from_file_name(file_path)

    if not federal_okrug:
        parent_folder = os.path.basename(os.path.dirname(file_path))
        federal_okrug = subfolder_to_okrug.get(parent_folder.lower())

    sheet_names_ = pd.ExcelFile(file_path).sheet_names
    sheet_names = []

    for name in sheet_names_:
        if name in fruit_allowed_names:
            sheet_names.append(name)

    combined_data = None

    for sheet_name in sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows)

        if not df.columns.astype(str).str.contains('ОПИСАНИЕ', case=False).any():
            log.error(f"Не удалось распарсить {file_path} - лист '{sheet_name}' в датафрейм")

        df.columns = [col.strip().capitalize() for col in df.columns]
        df.drop(columns=drop_cols, inplace=True, errors='ignore')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.rename(columns=old_column_mapping, inplace=True)

        if date_str:
            df["Дата"] = date_str

        if federal_okrug:
            df["federal_okrug"] = federal_okrug

        if combined_data is None:
            combined_data = df
        else:
            combined_data = pd.concat([combined_data, df], ignore_index=True)

    processed_df = combined_data.copy()
    processed_df['Цена'] = processed_df['Цена'].apply(process_price)
    processed_df['category'] = 'Фрукты'
    processed_df['Дата'] = pd.to_datetime(processed_df['Дата'], format="%d.%m.%Y")
    processed_df['week_number'] = processed_df['Дата'].dt.isocalendar().week
    processed_df['file_name'] = file_name
    processed_df.rename(columns=column_mapping, inplace=True)
    processed_df = processed_df.where(pd.notnull(processed_df), None)

    return processed_df
