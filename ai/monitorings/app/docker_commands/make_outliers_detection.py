from typing import Tuple

import click
import uuid
import os
from datetime import datetime, timedelta

import pandas as pd

from app.meat.processor.outliers_processor import predict_outliers_pipline
from app.meat.utils.data import MEAT, historical_columns
from app.utils.db import get_historical_data
from app.docker_commands.xcom_utils import docker_xcom_push


def _detect_meat(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Выполняет детекцию выбросов для данных мясной продукции.

    Загружает исторические данные за последние 90 дней и применяет
    пайплайн предсказания выбросов.

    Args:
        df: DataFrame с текущими данными мониторинга.

    Returns:
        Кортеж (обновлённый DataFrame, DataFrame с историческими данными).
    """
    date_from = datetime.now() - timedelta(days=90)
    historical_df = get_historical_data(category=MEAT, columns=historical_columns, date_from=date_from)
    return predict_outliers_pipline(df, historical_df)


@click.command()
@click.option("--source_file_path", help="Путь до исходного файла")
@click.option("--df_tmp_file_path", help="Путь до датафрейма")
@click.option("--monitoring_type", help="Тип обрабатываемого мониторинга")
def make_outliers_detection(source_file_path: str, df_tmp_file_path: str, monitoring_type: str) -> None:
    """Выполняет детекцию аномальных цен в данных мониторинга.

    Загружает DataFrame из временного файла, загружает исторические
    данные из БД, определяет выбросы и сохраняет результаты во
    временные файлы для текущего и исторического DataFrames.

    Args:
        source_file_path: Путь к исходному файлу мониторинга.
        df_tmp_file_path: Путь к временному файлу с DataFrame.
        monitoring_type: Тип мониторинга (поддерживается meat).
    """
    docker_xcom_push(source_file_path)
    docker_xcom_push(df_tmp_file_path)

    df = pd.read_csv(df_tmp_file_path, index_col=0)

    # детекция выбросов
    match monitoring_type:
        case 'meat':
            df, historical_df = _detect_meat(df)
        case _:
            raise KeyError(f'неподдерживаемый тип мониторинга {monitoring_type}')

    df.to_csv(df_tmp_file_path)
    historical_df_tmp_file_path = os.path.join('/opt/airflow/data', str(uuid.uuid4()))
    historical_df.to_csv(historical_df_tmp_file_path)

    docker_xcom_push(historical_df_tmp_file_path)


if __name__ == '__main__':
    make_outliers_detection()
