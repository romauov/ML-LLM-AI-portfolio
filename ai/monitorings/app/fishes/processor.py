import pandas as pd

from app.common.extractor import (extract_date_from_file_name, extract_federal_okrug_from_file_name,
                                  get_file_name_by_path)
from app.fishes.caviar.processor import process_caviar_dataframe_cols
from app.fishes.data import (
    column_mapping,
    drop_cols,
    fish_allowed_names,
    old_column_mapping,
)
from app.fishes.data_processor import process_dataframe_cols
from app.fishes.fish.processor import process_fish_dataframe_cols
from app.fishes.seafood.processor import process_seafood_dataframe_cols
from app.fishes.semiprocessed.processor import process_semiprocessed_dataframe_cols
from app.fishes.shrimp.processor import process_shrimp_dataframe_cols
from app.utils.logger import logger as log


def process_fish_file(file_path: str, skiprows: int = 8) -> pd.DataFrame:
    file_name = get_file_name_by_path(file_path, include_parent_name=False)

    # Отбор вкладок эксель файла
    sheet_names_ = pd.ExcelFile(file_path).sheet_names
    sheet_names = []
    if len(sheet_names_) == 1:
        sheet_names.append(0)
    else:
        for name in sheet_names_:
            if name.lower() in fish_allowed_names:
                sheet_names.append(name)
    combined_data = None
    for sheet_name in sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skiprows)

        # проверка парсинга датафрейма, меняем skiprows +- на несколько строк
        if not df.columns.astype(str).str.contains('Описание', case=False).any():
            result = False
            for shift in [1, -1, 2, -2]:
                if not result:
                    df = pd.read_excel(
                        file_path, sheet_name=sheet_name, skiprows=skiprows + shift)
                    if df.columns.astype(str).str.contains('Описание', case=False).any():
                        result = True
            if not result:
                log.error(
                    f"Не удалось распарсить {file_path} - {sheet_name} в датафрейм")

        df = df.iloc[1:]
        df.columns = [col.capitalize() for col in df.columns]
        df.drop(columns=drop_cols, inplace=True, errors='ignore')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df.rename(columns=old_column_mapping, inplace=True)

        date_str = extract_date_from_file_name(file_path)
        if date_str:
            df["Дата"] = date_str

        federal_okrug = extract_federal_okrug_from_file_name(file_path)
        if federal_okrug:
            df["federal_okrug"] = federal_okrug

        if combined_data is None:
            combined_data = df
        else:
            combined_data = pd.concat(
                [combined_data, df], ignore_index=True)

    processed_df = process_dataframe_cols(combined_data)
    processed_df['category'] = 'Рыба и морепродукты'
    processed_df['Дата'] = pd.to_datetime(processed_df['Дата'], format="%d.%m.%Y")
    processed_df['week_number'] = processed_df['Дата'].dt.isocalendar().week
    processed_df['file_name'] = file_name
    processed_df.rename(columns=column_mapping, inplace=True)

    dfs = []
    fish_df = processed_df[processed_df['product'] == 'Рыба']
    if not fish_df.empty:
        dfs.append(process_fish_dataframe_cols(fish_df))

    caviar_df = processed_df[processed_df['product'] == 'Икра']
    if not caviar_df.empty:
        dfs.append(process_caviar_dataframe_cols(caviar_df))

    shrimp_df = processed_df[processed_df['product'] == 'Креветки']
    if not shrimp_df.empty:
        dfs.append(process_shrimp_dataframe_cols(shrimp_df))

    seafood_df = processed_df[processed_df['product'] == 'Морепродукты']
    if not seafood_df.empty:
        dfs.append(process_seafood_dataframe_cols(seafood_df))

    semiprocessed_df = processed_df[processed_df['product'] == 'Полуфабрикаты']
    if not semiprocessed_df.empty:
        dfs.append(process_semiprocessed_dataframe_cols(semiprocessed_df))

    df_concat = pd.concat(dfs, ignore_index=True)
    return df_concat
