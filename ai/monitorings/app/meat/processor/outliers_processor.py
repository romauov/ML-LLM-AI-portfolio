from typing import Tuple
import warnings

import pandas as pd
from pandas.errors import SettingWithCopyWarning

from app.common.models.outliers_detection import (panel_ols_predict, lof_predict, isolation_forest_predict,
                                                  z_score_predict, iqr_predict)
from app.meat.utils.pandas_utils import dataframe_columns_to_json_string, pandas_label_encode
from app.utils.logger import logger as log

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)


def prepare_dataframe(df_: pd.DataFrame) -> pd.DataFrame:
    """Подготавливает DataFrame для анализа выбросов.

    Выполняет предварительную обработку данных: создаёт составной идентификатор,
    фильтрует группы с недостаточным количеством наблюдений, преобразует дату,
    выполняет кодирование категориальных признаков и рассчитывает статистики
    по компаниям.

    Args:
        df_: Исходный DataFrame с данными о ценах.

    Returns:
        Обработанный DataFrame с добавленными признаками и отфильтрованными группами.
    """
    df = df_.copy()

    df['ID'] = dataframe_columns_to_json_string(df, ['product', 'product_type', 'federal_okrug'])
    df = df.groupby('ID').filter(lambda g: len(g) > 30)
    df['date'] = pd.to_datetime(df['date'], format="%d.%m.%Y")

    df['temperature_state'], _ = pandas_label_encode(df, 'temperature_state', 0)
    df['sort'], _ = pandas_label_encode(df, 'sort', 0)
    df['certification'], _ = pandas_label_encode(df, 'certification', 0)
    df['company'], _ = pandas_label_encode(df, 'company', 200)
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['year'], _ = pandas_label_encode(df, 'year', 0)
    df['month'], _ = pandas_label_encode(df, 'month', 0)

    df['company_mean_price'] = df.groupby(['ID', 'company'])['price'].transform('mean')
    df['company_median_price'] = df.groupby(['ID', 'company'])['price'].transform('median')
    df['company_count'] = df.groupby(['ID', 'company'])['price'].transform('count')
    df['company_std_price'] = df.groupby(['ID', 'company'])['price'].transform('std').fillna(0)

    return df


def make_is_outlier_decision(
        df: pd.DataFrame,
        category_column: str,
        indicator_column: str
) -> pd.Series:
    """Определяет, является ли наблюдение выбросом, на основе адаптивного порога.

    Для каждой категории вычисляет динамический порог на основе доли
    потенциальных выбросов. Если выбросов много, порог повышается,
    и наоборот.

    Args:
        df: DataFrame с данными и индикатором выбросов.
        category_column: Имя столбца для группировки по категориям.
        indicator_column: Имя столбца с количеством моделей, определивших выброс.

    Returns:
        Series с булевыми значениями: True если наблюдение является выбросом.
    """
    df_copy = df.copy()
    for cat in df[category_column].unique().tolist():
        df_ = df[df[category_column] == cat]

        total_points = len(df)
        outlier_points = len(df_[df_[indicator_column] < 2])

        if outlier_points > total_points * 0.5:
            threshold = 4
        elif outlier_points > total_points * 0.25:
            threshold = 3
        else:
            threshold = 2

        df_copy.loc[df_.index, 'is_outlier'] = df_[indicator_column] >= threshold
    return df_copy['is_outlier']


def predict_outliers_by_all_models(df_: pd.DataFrame) -> pd.Series:
    """Прогнозирует выбросы с использованием ансамбля моделей.

    Применяет пять различных методов обнаружения выбросов: панельная регрессия,
    LOF, изолирующий лес, Z-score и IQR. Решение о выбросе принимается
    на основе адаптивного порога по количеству моделей, согласившихся с выбросом.

    Args:
        df_: Подготовленный DataFrame с признаками для анализа.

    Returns:
        Series с булевыми значениями: True если наблюдение является выбросом.
    """
    df = df_.copy()

    try:
        df['panel_ols_outlier'] = panel_ols_predict(
            df=df, category_column='ID', date_column='date', target_column='price', mu=2,
            exog_vars=["temperature_state", "sort", "certification", "company", 'month'],
            entity_effects=True, time_effects=True
        )
    except Exception as e:
        log.info(f'что-то пошло не так {e}')
        df['panel_ols_outlier'] = False

    df['lof_outlier'] = lof_predict(
        df=df, category_column='ID', n_neighbors=20, contamination="auto",
        feature_names=['price', 'company_mean_price', 'company_median_price', 'company_count', 'company_std_price']
    )

    df['isf_outlier'] = isolation_forest_predict(
        df=df, n_estimators=250, max_samples="auto", contamination="auto", max_features=1.0, bootstrap=True,
        feature_names=['ID', 'price', 'company_mean_price', 'company_median_price', 'company_count',
                       'company_std_price']
    )

    df['z_score_outlier'] = z_score_predict(df=df, category_column='ID', target_column='price', mu=2)
    df['iqr_outlier'] = iqr_predict(df=df, category_column='ID', target_column='price')

    outliers_columns = ['panel_ols_outlier', 'lof_outlier', 'isf_outlier', 'z_score_outlier', 'iqr_outlier']
    df['outlier_count'] = df[outliers_columns].sum(axis=1)

    df['is_outlier'] = make_is_outlier_decision(df=df, category_column='ID', indicator_column='outlier_count')
    return df['is_outlier']


def predict_outliers_pipline(
        new_df: pd.DataFrame,
        historical_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Выполняет полный пайплайн обнаружения выбросов для новых и исторических данных.

    Объединяет новые и исторические данные, выполняет предобработку,
    прогнозирование выбросов с помощью ансамбля моделей и разделяет
    результаты обратно на новые и исторические предсказания.

    Args:
        new_df: DataFrame с новыми данными для анализа.
        historical_df: DataFrame с историческими данными для контекста.

    Returns:
        Кортеж из двух DataFrame: предсказания для новых данных и предсказания
        для исторических данных с индексом db_id.
    """
    historical_df.reset_index(names='db_id', inplace=True)

    df = pd.concat((new_df, historical_df), axis=0).reset_index(drop=True)

    prepared_df = prepare_dataframe(df)
    prepared_df['is_outlier'] = predict_outliers_by_all_models(prepared_df)
    df.loc[prepared_df.index, 'is_outlier'] = prepared_df['is_outlier']

    df['is_outlier'].fillna(False, inplace=True)

    new_df_preds = df[df['db_id'].isna()].reset_index(drop=True)
    new_df_preds.drop('db_id', axis=1, inplace=True)
    historical_df_preds = df[~df['db_id'].isna()].set_index('db_id')
    historical_df_preds.index.name = 'id'

    return new_df_preds, historical_df_preds
