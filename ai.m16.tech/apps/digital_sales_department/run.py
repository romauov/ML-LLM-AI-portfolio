"""
Команды для обучения модели

python -m digital_sales_department.run download-db - Загрузка датасета из базы данных
python -m digital_sales_department.run train - Обучение модели
python -m digital_sales_department.run test - Проверка модели

@author Sergey Goncharov
"""

import click

from digital_sales_department.dataset import load_dataset_from_db
from digital_sales_department.user_interest import train_model, user_interest_prediction


@click.group()
def cli():
    """
    Создание группы для команд
    """


@click.command()
def download_db():
    """
    Загрузка датасета из базы данных
    """
    load_dataset_from_db()


@click.command()
def train():
    """
    Обучение модели
    """
    train_model()


@click.command()
@click.argument('user_id')
def test(user_id: int):
    """
    Проверка модели
    """
    users = [user_id]
    result = user_interest_prediction(users)
    print(result)


cli.add_command(download_db)
cli.add_command(train)
cli.add_command(test)

cli()
