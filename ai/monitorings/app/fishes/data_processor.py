import pandas as pd

from app.common.processor import process_price


def process_dataframe_cols(df):
    df = df.copy()
    if 'Наименование, описание' in df.columns:
        df.rename(columns={'Наименование, описание': 'Описание'}, inplace=True)
    if 'Наименование' in df.columns:
        df.rename(columns={'Наименование': 'Категория'}, inplace=True)

    df = df.astype({'Описание': str, 'Категория': str})
    df['Категория'] = df['Категория'].str.capitalize()
    df = df.dropna(subset=['Категория'])
    df = df[df['Описание'].str.strip() != '']
    df['Цена'] = df['Цена'].apply(process_price)

    df["Дата"] = pd.to_datetime(df["Дата"], format="%d.%m.%Y", errors="coerce")
    df = df.sort_values("Дата")
    return df
