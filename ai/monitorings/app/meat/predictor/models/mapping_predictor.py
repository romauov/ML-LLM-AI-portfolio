"""
Скрипты для обхода файлов в папке с мониториингами и их перемещения

@author Sergei Romanov
"""
import os

import pandas as pd


def predict_on_mapping(df):
    """предсказание product_type по таблице соответствий

    Args:
        df (DataFrame): датафрейм мониторинга

    Returns:
        DataFrame: датафрейм мониторинга с предсказаниями
    """
    df.loc[:, 'description'] = df['description'].astype(str)
    df.loc[:, 'description_ls'] = df['description'].apply(lambda x: x.lower().strip())

    df_map = pd.read_csv(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'meat_dataset_v4.csv'),
        index_col=0,
        sep=';'
    )
    df_map = df_map.dropna(subset=['product_type'])
    df_map['description_ls'] = df_map['description'].apply(lambda x: x.lower().strip())
    df_map = df_map[['description_ls', 'product', 'product_type']]
    df_map = df_map.drop_duplicates('description_ls')

    df_merged = pd.merge(df, df_map, on=['product', 'description_ls'], how='left', validate='many_to_one')
    return df_merged
