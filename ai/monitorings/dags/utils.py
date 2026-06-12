import os
import logging
import shutil
from typing import Tuple, List

from airflow.sdk import Context

logger = logging.getLogger(__name__)


def check_files_exist(dir_name: str, file_extensions: Tuple[str, ...]) -> bool:
    """Проверяет наличие хотя бы одного файла с указанными расширениями в директории.

    Args:
        dir_name: Путь к директории для проверки.
        file_extensions: Кортеж расширений файлов для поиска (например, ('.xlsx', '.xls')).

    Returns:
        True если найден хотя бы один подходящий файл, иначе False.
    """
    for root, _, files in os.walk(dir_name):
        for f in files:
            if f.endswith(file_extensions):
                return True
    return False


def collect_files(dir_name: str, file_extensions: Tuple[str, ...]) -> List[str]:
    """Собирает все файлы с указанными расширениями в директории и её подкаталогах.

    Args:
        dir_name: Путь к директории для поиска.
        file_extensions: Кортеж расширений файлов для поиска (например, ('.xlsx', '.xls')).

    Returns:
        Список полных путей к найденным файлам.
    """
    files = []
    for root, _, dir_files in os.walk(dir_name):
        for f in dir_files:
            if f.endswith(file_extensions):
                file_path = os.path.join(root, f)
                files.append(file_path)

    return files


def on_success_move_file(context: Context) -> None:
    """Callback для перемещения исходного файла в папку успешной обработки.

    Извлекает путь к исходному файлу из XCom и перемещает его
    из source_folder в success_destination, сохраняя структуру подкаталогов.

    Args:
        context: Контекст выполнения задачи Airflow.
    """
    logging.info('execute success callback')

    ti = context['task_instance']
    data = ti.xcom_pull(key='return_value', task_ids=ti.task_id, map_indexes=ti.map_index)

    # достаем из данных путь до файла источника данных
    if isinstance(data, tuple) or isinstance(data, list):
        source_file = data[0]
    else:
        source_file = data

    source_folder = context['params']['source_folder']
    success_destination = context['params']['success_destination']

    if source_file.startswith(source_folder):
        _move_file(source_file, source_folder, success_destination)
    else:
        logger.warning(f'first xcom file is not source file: {source_file}')


def on_failure_move_file(context: Context) -> None:
    """Callback для перемещения исходного файла в папку ошибок.

    Извлекает путь к исходному файлу из XCom и перемещает его
    из source_folder в failure_destination, сохраняя структуру подкаталогов.

    Args:
        context: Контекст выполнения задачи Airflow.
    """
    logging.info('execute failure callback')

    ti = context['task_instance']
    data = ti.xcom_pull(key='return_value', task_ids=ti.task_id, map_indexes=ti.map_index)

    # достаем из данных путь до файла источника данных
    if isinstance(data, tuple) or isinstance(data, list):
        source_file = data[0]
    else:
        source_file = data

    source_folder = context['params']['source_folder']
    failure_destination = context['params']['failure_destination']

    if source_file.startswith(source_folder):
        _move_file(source_file, source_folder, failure_destination)
    else:
        logger.warning(f'first xcom file is not source file: {source_file}')


def clean_up_temp_files(context: Context) -> None:
    """Callback для удаления временных файлов после выполнения задачи.

    Извлекает пути к временным файлам из XCom и удаляет их,
    если они находятся внутри указанной временной папки.

    Args:
        context: Контекст выполнения задачи Airflow.
    """
    logging.info('execute clean up tmp files callback')

    ti = context['task_instance']
    data = ti.xcom_pull(key='return_value', task_ids=ti.task_id, map_indexes=ti.map_index)

    if isinstance(data, str):
        data = [data]

    tmp_folder = context['params']['tmp_folder']

    for item in data:
        if item.startswith(tmp_folder):
            os.remove(item)
            logging.info(f'deleted tmp file {item}')


def _move_file(source_file: str, source_folder: str, destination_folder: str) -> None:
    """Перемещает файл в целевую папку, сохраняя относительную структуру подкаталогов.

    Args:
        source_file: Полный путь к исходному файлу.
        source_folder: Базовая папка-источник (для расчёта относительного пути).
        destination_folder: Целевая папка для перемещения.
    """
    relative_path = str(os.path.relpath(os.path.dirname(source_file), source_folder))
    new_subfolder_path = os.path.join(destination_folder, relative_path)
    os.makedirs(new_subfolder_path, exist_ok=True)
    new_path = os.path.join(new_subfolder_path, os.path.basename(source_file))
    shutil.move(source_file, new_path)
