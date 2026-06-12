import click
import uuid
import os

import pandas as pd

from app.egg.processor import process_egg_file
from app.fishes.processor import process_fish_file
from app.fruit.processor import process_fruit_file
from app.meat.processor.processor import process_from_csv, process_from_excel
from app.milk.processor import process_milk_file
from app.docker_commands.xcom_utils import docker_xcom_push


def _process_meat(source_file_path: str) -> pd.DataFrame:
    """Обрабатывает файл мониторинга мясной продукции.

    Args:
        source_file_path: Путь к исходному файлу (.csv, .xlsx или .xls).

    Returns:
        DataFrame с извлечёнными и нормализованными данными.
    """
    if source_file_path.endswith('.csv'):
        df = process_from_csv(source_file_path)
    elif source_file_path.endswith('.xlsx') or source_file_path.endswith('.xls'):
        df = process_from_excel(source_file_path)
    else:
        raise KeyError(f'неподдерживаемый тип файла {source_file_path}')

    return df


@click.command()
@click.option("--source_file_path", help="Путь до обрабатываемого файла мониторинга")
@click.option("--monitoring_type", help="Тип обрабатываемого мониторинга")
def make_process_file(source_file_path: str, monitoring_type: str) -> None:
    """Обрабатывает файл мониторинга и сохраняет результат во временный CSV.

    Извлекает данные из файла в зависимости от типа мониторинга,
    сохраняет промежуточный DataFrame во временный файл и передаёт
    его путь через XCom для последующих шагов пайплайна.

    Args:
        source_file_path: Путь к исходному файлу мониторинга.
        monitoring_type: Тип мониторинга (meat, milk, fruit, fish, egg).
    """
    docker_xcom_push(source_file_path)

    match monitoring_type:
        case 'meat':
            df = _process_meat(source_file_path)
        case 'milk':
            df = process_milk_file(source_file_path)
        case 'fruit':
            df = process_fruit_file(source_file_path)
        case 'fish':
            df = process_fish_file(source_file_path)
        case 'egg':
            df = process_egg_file(source_file_path)
        case _:
            raise KeyError(f'неподдерживаемый тип мониторинга {monitoring_type}')

    df_tmp_file_path = os.path.join('/opt/airflow/data', str(uuid.uuid4()))
    df.to_csv(df_tmp_file_path)

    docker_xcom_push(df_tmp_file_path)


if __name__ == '__main__':
    make_process_file()
