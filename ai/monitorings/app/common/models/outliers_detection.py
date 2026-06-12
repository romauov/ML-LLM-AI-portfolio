from typing import List, Union
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.panel import PanelOLS
from linearmodels.panel.utility import AbsorbingEffectWarning
from sklearn.neighbors import LocalOutlierFactor
from sklearn.ensemble import IsolationForest
from pandas.errors import SettingWithCopyWarning

from app.meat.utils.pandas_utils import pandas_label_encode

warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)
warnings.simplefilter(action='ignore', category=AbsorbingEffectWarning)
warnings.simplefilter(action='ignore', category=UserWarning)


def panel_ols_predict(
        df: pd.DataFrame,
        category_column: str,
        date_column: str,
        target_column: str,
        exog_vars: List[str],
        mu: int,
        entity_effects: bool = True,
        time_effects: bool = False,
) -> pd.Series:
    """Обнаружение выбросов с помощью панельной регрессии с фиксированными эффектами.

    Оценивается модель панельной регрессии с фиксированными эффектами
    (entity и/или time), затем наблюдения, стандартизованные остатки которых
    превышают заданный порог (mu), помечаются как выбросы.

    Args:
        df: Входной DataFrame с панельными данными.
        category_column: Имя столбца, идентифицирующего кросс-секционные единицы.
        date_column: Имя столбца, идентифицирующего временные периоды.
        target_column: Имя столбца зависимой переменной.
        exog_vars: Список имён столбцов экзогенных (независимых) переменных.
        mu: Количество стандартных отклонений для порога отсечения.
        entity_effects: Включать ли фиксированные эффекты единиц. По умолчанию True.
        time_effects: Включать ли фиксированные эффекты времени. По умолчанию False.

    Returns:
        Булева Series с именем 'panel_ols_outlier', где True означает,
        что наблюдение является выбросом, а False — что нет.
        Индексация совпадает с исходным DataFrame.
    """
    df_copy = df.copy()

    df_copy.reset_index(inplace=True)
    df_copy.set_index([category_column, date_column], inplace=True)  # Устанавливаем MultiIndex
    exog = sm.add_constant(df_copy[exog_vars])

    fe_te_model = PanelOLS(
        dependent=df_copy[target_column],
        exog=exog,
        entity_effects=entity_effects,
        time_effects=time_effects,
        drop_absorbed=True,
        check_rank=False,
    )
    fe_te_res = fe_te_model.fit(
        cov_type='clustered',
        cluster_entity=True,
        auto_df=True,
    )

    df_copy['resids'] = fe_te_res.resids
    df_copy['std_resid'] = df_copy['resids'] / fe_te_res.resids.std()

    df_copy.reset_index(inplace=True)  # убираем MultiIndex чтобы подсчитать статистику
    df_copy['panel_ols_outlier'] = np.abs(df_copy.reset_index()['std_resid']) > mu
    df_copy.set_index('index', inplace=True)  # возвращаем изначальный индекс

    return df_copy['panel_ols_outlier']


def lof_predict(
        df: pd.DataFrame,
        category_column: str,
        feature_names: List[str],
        n_neighbors: int,
        contamination: Union[float, str] = "auto"
) -> pd.Series:
    """Обнаружение выбросов с помощью алгоритма Local Outlier Factor (LOF).

    Модель LOF обучается отдельно внутри каждой категории. Алгоритм измеряет
    отклонение локальной плотности каждого наблюдения относительно его соседей.
    Наблюдения с более низкой локальной плотностью, чем у соседей,
    помечаются как выбросы.

    Args:
        df: Входной DataFrame с данными для анализа.
        category_column: Имя столбца для группировки данных.
            Модель LOF обучается независимо внутри каждой категории.
        feature_names: Список имён столбцов-признаков для обнаружения выбросов.
        n_neighbors: Количество соседей, используемых для вычисления LOF.
        contamination: Ожидаемая доля выбросов в данных.
            Если "auto", порог определяется автоматически. По умолчанию "auto".

    Returns:
        Булева Series с именем 'lof_outlier', где True означает,
        что наблюдение является выбросом, а False — что нет.
        Индексация совпадает с исходным DataFrame.
    """
    df_copy = df.copy()
    for cat in df_copy[category_column].unique().tolist():
        df_ = df_copy[df_copy[category_column] == cat]

        lof = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination
        )
        lof_pred = lof.fit_predict(df_[feature_names])
        df_copy.loc[df_.index, 'lof_outlier'] = lof_pred

    df_copy.fillna({'lof_outlier': 1}, inplace=True)
    df_copy['lof_outlier'].replace([1, -1], [False, True], inplace=True)
    return df_copy['lof_outlier']


def isolation_forest_predict(
        df: pd.DataFrame,
        feature_names: List[str],
        n_estimators: int = 250,
        max_samples: Union[float, str] = 'auto',
        contamination: Union[float, str] = "auto",
        max_features: float = 1.0,
        bootstrap: bool = True
) -> pd.Series:
    """Обнаружение выбросов с помощью алгоритма Isolation Forest.

    Строится ансамбль изолирующих деревьев, которые рекурсивно разделяют данные,
    случайным образом выбирая признак и значение разбиения. Аномалии изолируются
    ближе к корню дерева, что даёт более короткую длину пути. Наблюдения
    с меньшей средней длиной пути по всем деревьям помечаются как выбросы.

    Args:
        df: Входной DataFrame с данными для анализа.
        feature_names: Список имён столбцов-признаков для обнаружения выбросов.
        n_estimators: Количество базовых оценок (деревьев) в лесу.
            По умолчанию 250.
        max_samples: Количество выборок для построения каждого базового оценщика.
            Если 'auto', используется min(256, n_samples). По умолчанию 'auto'.
        contamination: Ожидаемая доля выбросов в данных.
            Если "auto", порог определяется автоматически. По умолчанию "auto".
        max_features: Доля признаков, используемых для каждого дерева.
            По умолчанию 1.0 (все признаки).
        bootstrap: Производить ли сэмплирование с возвращением при построении
            деревьев. По умолчанию True.

    Returns:
        Булева Series с именем 'isf_outlier', где True означает,
        что наблюдение является выбросом, а False — что нет.
        Индексация совпадает с исходным DataFrame.
    """
    df_copy = df.copy()
    df_copy['ID'], id_categories = pandas_label_encode(df_copy, 'ID', 0)
    isf = IsolationForest(
        n_estimators=n_estimators,
        max_samples=max_samples,
        contamination=contamination,
        max_features=max_features,
        bootstrap=bootstrap
    )
    isf_preds = isf.fit_predict(X=df_copy[feature_names])

    return pd.Series(isf_preds == -1, index=df_copy.index, name="isf_outlier")


def z_score_predict(
        df: pd.DataFrame,
        category_column: str,
        target_column: str,
        mu: int
) -> pd.Series:
    """Обнаружение выбросов с помощью метода Z-score по каждой категории.

    Для каждой категории отдельно вычисляются медиана как мера центральной
    тенденции и среднее абсолютное отклонение от среднего как мера разброса.
    Наблюдения, Z-score которых превышает заданный порог (mu),
    помечаются как выбросы.

    Args:
        df: Входной DataFrame с данными для анализа.
        category_column: Имя столбца для группировки данных.
            Статистика вычисляется независимо внутри каждой категории.
        target_column: Имя столбца со значениями для проверки.
        mu: Количество стандартных отклонений для порога отсечения.

    Returns:
        Булева Series с именем 'z_outlier', где True означает,
        что наблюдение является выбросом, а False — что нет.
        Индексация совпадает с исходным DataFrame.
    """
    df_copy = df.copy()

    mean = df_copy.groupby(category_column)[target_column].transform("median")
    std = df_copy.groupby(category_column)[target_column].transform(lambda x: (x - x.mean()).abs().mean())
    df_copy["z_outlier"] = (df_copy[target_column] - mean).abs() > mu * std
    return df_copy["z_outlier"]


def iqr_predict(
        df: pd.DataFrame,
        category_column: str,
        target_column: str,
) -> pd.Series:
    """Обнаружение выбросов с помощью метода межквартильного размаха (IQR) по каждой категории.

    Для каждой категории отдельно вычисляются первый квартиль (Q1),
    третий квартиль (Q3) и межквартильный размах (IQR = Q3 - Q1).
    Наблюдения, выходящие за пределы [Q1 - 1.5×IQR, Q3 + 1.5×IQR],
    помечаются как выбросы.

    Args:
        df: Входной DataFrame с данными для анализа.
        category_column: Имя столбца для группировки данных.
            Статистика вычисляется независимо внутри каждой категории.
        target_column: Имя столбца со значениями для проверки.

    Returns:
        Булева Series с именем 'iqr_outlier', где True означает,
        что наблюдение является выбросом, а False — что нет.
        Индексация совпадает с исходным DataFrame.
    """
    df_copy = df.copy()

    q1 = df_copy.groupby(category_column)[target_column].transform("quantile", 0.25)
    q3 = df_copy.groupby(category_column)[target_column].transform("quantile", 0.75)
    iqr = q3 - q1
    df_copy["iqr_outlier"] = (df_copy[target_column] < q1 - 1.5 * iqr) | (df_copy[target_column] > q3 + 1.5 * iqr)

    return df_copy["iqr_outlier"]
