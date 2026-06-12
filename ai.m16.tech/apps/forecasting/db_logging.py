"""
Проверка результатов в базе данных, запись параметров прогнозирования в БД

@author Dmitry Abramov
"""
import datetime

from sqlalchemy import insert, select, create_engine, Table, MetaData, desc
import pandas as pd


# pylint: disable=too-many-arguments
def exist_checker(ds_col, y_col, steps, validation_steps, trials,
                  temp_file, n_ensemble, date_border, sheet_name, years):
    """
    Проверка запроса в базе данных, в случае нахождения возвращается путь директории

    Принимает:
        Параметры, указываемые для Pipeline прогнозирования со страницы Gradio

    Возвращает:
        Количество найденных записей в БД по переданным параметрам: int
        Путь к директории результатов: str
        id запуска: int
    """
    engine = create_engine("postgresql+psycopg2://airflow:airflow@postgres:5432/forecasting")

    metadata = MetaData()

    table = Table('forecasting_data', metadata, autoload_with=engine)
    stmt = select(table.c.id, table.c.dir_path).where(table.c.ds_col == ds_col,
                                                      table.c.y_col == y_col,
                                                      table.c.steps == steps,
                                                      table.c.validation_steps == validation_steps,
                                                      table.c.trials == trials,
                                                      table.c.file_name == temp_file,
                                                      table.c.n_ensemble == n_ensemble,
                                                      table.c.date_border == date_border,
                                                      table.c.sheet_name == sheet_name,
                                                      table.c.years == years)
    with engine.connect() as conn:
        query = conn.execute(stmt)
    result = list(query)
    if len(result) == 0:
        return len(result), [], None
    return len(result), result[-1][1], result[-1][0]


def insert_row(ds_col, y_col, steps, validation_steps, trials,
               temp_file, n_ensemble, date_border, sheet_name, years, dir_path):
    """
    Запись в базу данных Postgres полученных параметров и пути к директории результатов

    Возвращает:
        int - id записи
    """
    engine = create_engine("postgresql+psycopg2://airflow:airflow@postgres:5432/forecasting")

    with engine.connect() as conn:

        metadata = MetaData()
        result = conn.execute(
            insert(Table('forecasting_data', metadata, autoload_with=engine)),
            {
                'ds_col': ds_col,
                'y_col': y_col,
                'steps': steps,
                'validation_steps': validation_steps,
                'trials': trials,
                'file_name': temp_file,
                'n_ensemble': n_ensemble,
                'date_border': date_border,
                'sheet_name': sheet_name,
                'years': years,
                'dir_path': dir_path,
                'datetime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                )
        conn.commit()
    # id добавленной записи
    return result.inserted_primary_key[0]

def result_getting(_id):
    """
    Получение директории результата по id запуска

    Принимает: 
        _id: int - id запуска прогнозирования
    Возвращает:
        Количество найденных записей в БД по переданным параметрам: int
        Путь к директории результатов: str
    """
    engine = create_engine("postgresql+psycopg2://airflow:airflow@postgres:5432/forecasting")
    metadata = MetaData()

    table = Table('forecasting_data', metadata, autoload_with=engine)
    stmt = select(table.c.dir_path).where(table.c.id == _id)

    with engine.connect() as conn:
        query = conn.execute(stmt)

    result = list(query)

    if len(result) == 0:
        return len(result), []
    return len(result), result[0][0]


def db_rows(rows: int):
    """
    Записи в бд с успешными запусками прогнозов

    Принимает: 
        rows: int - количество последних записей
    Возвращает:
        Количество найденных записей в БД по переданным параметрам: int
        Путь к директории результатов: str
    """
    engine = create_engine("postgresql+psycopg2://airflow:airflow@postgres:5432/forecasting")
    metadata = MetaData()
    table = Table('forecasting_data', metadata, autoload_with=engine)
    stmt = select(table.c.id, table.c.ds_col, table.c.y_col, table.c.steps,
                  table.c.file_name, table.c.sheet_name,
                  table.c.years, table.c.dir_path, table.c.datetime).order_by(desc(table.c.id)).limit(rows)

    with engine.connect() as conn:
        query = conn.execute(stmt)
    return pd.DataFrame(query.fetchall())
