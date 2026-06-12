import click
import pandas as pd

from app.meat.predictor.predictor import make_predictions
from app.docker_commands.xcom_utils import docker_xcom_push


@click.command()
@click.option("--source_file_path", help="Путь до исходного файла")
@click.option("--df_tmp_file_path", help="Путь до датафрейма")
@click.option("--monitoring_type", help="Тип обрабатываемого мониторинга")
def make_classification(source_file_path: str, df_tmp_file_path: str, monitoring_type: str) -> None:
    """Выполняет классификацию product_type для данных мониторинга.

    Загружает DataFrame из временного файла, применяет ML-модель
    для предсказания product_type и перезаписывает файл обновлёнными данными.

    Args:
        source_file_path: Путь к исходному файлу мониторинга.
        df_tmp_file_path: Путь к временному файлу с DataFrame.
        monitoring_type: Тип мониторинга (поддерживается meat).
    """
    docker_xcom_push(source_file_path)
    docker_xcom_push(df_tmp_file_path)

    df = pd.read_csv(df_tmp_file_path, index_col=0)

    match monitoring_type:
        case 'meat':
            df = make_predictions(df)
        case _:
            raise KeyError(f'неподдерживаемый тип мониторинга {monitoring_type}')

    df.to_csv(df_tmp_file_path)


if __name__ == '__main__':
    make_classification()
