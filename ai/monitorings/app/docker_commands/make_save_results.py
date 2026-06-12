from typing import Optional

import click
import pandas as pd

from app.common.extractor import get_file_name_by_path
from app.egg.data import EGG
from app.fishes.caviar.data import caviar_expected_columns
from app.fishes.fish.data import fish_expected_columns
from app.fishes.seafood.data import seafood_expected_columns
from app.fishes.semiprocessed.data import semiprocessed_expected_columns
from app.fishes.shrimp.data import shrimp_expected_columns
from app.fruit.data import FRUIT
from app.meat.utils.data import MEAT
from app.milk.data import MILK
from app.utils.db import upload_to_mysql, update_table_data_by_id
from app.docker_commands.xcom_utils import docker_xcom_push


def _save_meat(df: pd.DataFrame, source_name: str, historical_df_tmp_file_path: str) -> None:
    """Сохраняет данные мониторинга мясной продукции в БД.

    Args:
        df: DataFrame с обработанными данными.
        source_name: Имя исходного файла.
        historical_df_tmp_file_path: Путь к временному файлу с историческими данными
            для обновления меток выбросов. Может быть None.
    """
    upload_to_mysql(df=df, category=MEAT, source_name=source_name)

    if historical_df_tmp_file_path:
        historical_df = pd.read_csv(historical_df_tmp_file_path, index_col=0)
        update_table_data_by_id(category=MEAT, df=historical_df['is_outlier'])


def _save_fish(df: pd.DataFrame, source_name: str) -> None:
    """Сохраняет данные мониторинга рыбной продукции в БД по категориям.

    Разделяет DataFrame по продуктам (рыба, икра, креветки, морепродукты,
    полуфабрикаты) и загружает каждую категорию в соответствующую таблицу.

    Args:
        df: DataFrame с обработанными данными.
        source_name: Имя исходного файла.
    """
    fish_df = df[df['product'] == 'Рыба']
    if not fish_df.empty:
        upload_to_mysql(df=fish_df[fish_expected_columns], category='fish', source_name=source_name)

    caviar_df = df[df['product'] == 'Икра']
    if not caviar_df.empty:
        upload_to_mysql(df=caviar_df[caviar_expected_columns], category='caviar', source_name=source_name)

    shrimp_df = df[df['product'] == 'Креветки']
    if not shrimp_df.empty:
        upload_to_mysql(df=shrimp_df[shrimp_expected_columns], category='shrimp', source_name=source_name)

    seafood_df = df[df['product'] == 'Морепродукты']
    if not seafood_df.empty:
        upload_to_mysql(df=seafood_df[seafood_expected_columns], category='seafood', source_name=source_name)

    semiprocessed_df = df[df['product'] == 'Полуфабрикаты']
    if not semiprocessed_df.empty:
        upload_to_mysql(
            df=semiprocessed_df[semiprocessed_expected_columns], category='semiprocessed', source_name=source_name
        )


@click.command()
@click.option("--source_file_path", help="Путь до исходного файла")
@click.option("--df_tmp_file_path", help="Путь до датафрейма")
@click.option("--historical_df_tmp_file_path", help="Путь до датафрейма с историческими данными из бд")
@click.option("--monitoring_type", help="Тип обрабатываемого мониторинга")
def make_save_results(
        source_file_path: str,
        df_tmp_file_path: str,
        monitoring_type: str,
        historical_df_tmp_file_path: Optional[str] = None,
) -> None:
    """Сохраняет результаты обработки мониторинга в базу данных MySQL.

    Загружает обработанный DataFrame из временного файла и сохраняет
    данные в БД в зависимости от типа мониторинга. Для мясной продукции
    дополнительно обновляет метки выбросов в исторических данных.

    Args:
        source_file_path: Путь к исходному файлу мониторинга.
        df_tmp_file_path: Путь к временному файлу с DataFrame.
        monitoring_type: Тип мониторинга (meat, milk, fruit, fish, egg).
        historical_df_tmp_file_path: Путь к файлу с историческими данными (для meat).
    """
    docker_xcom_push(source_file_path)
    docker_xcom_push(df_tmp_file_path)
    docker_xcom_push(historical_df_tmp_file_path)

    df = pd.read_csv(df_tmp_file_path, index_col=0)
    file_name = get_file_name_by_path(source_file_path, include_parent_name=False)

    match monitoring_type:
        case 'meat':
            _save_meat(df, file_name, historical_df_tmp_file_path)
        case 'milk':
            upload_to_mysql(df=df, category=MILK, source_name=file_name)
        case 'fruit':
            upload_to_mysql(df=df, category=FRUIT, source_name=file_name)
        case 'fish':
            _save_fish(df=df, source_name=file_name)
        case 'egg':
            upload_to_mysql(df=df, category=EGG, source_name=file_name)
        case _:
            raise KeyError(f'неподдерживаемый тип мониторинга {monitoring_type}')


if __name__ == '__main__':
    make_save_results()
