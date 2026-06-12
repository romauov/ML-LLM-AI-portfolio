"""
Скрипт отправки данных мониторингов в БД

@author Sergei Romanov
"""
from typing import List, Optional, Tuple
from datetime import datetime

from sqlalchemy import insert, select, update, bindparam, delete
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import Table
import pandas as pd

from app.utils.data import raw_tables
from app.utils.db_sessions import db_manager, manage_sessions
from app.utils.logger import logger as log


@manage_sessions()
def upload_table(
    session: Session,
    df: pd.DataFrame,
    table: Table,
    source_name: Optional[str] = None
) -> None:
    """Построчная загрузка и обновление данных в базе данных.

    Удаляет существующие записи с указанным именем файла и вставляет
    новые строки из DataFrame.

    Args:
        session: сессия базы данных, предоставляемая декоратором manage_sessions
        df: датафрейм с данными мониторинга для загрузки
        table: таблица SQLAlchemy для вставки данных
        source_name: имя исходного файла для фильтрации удаляемых записей

    Returns:
        None
    """

    delete_count = 0
    if source_name:
        stmt = delete(table).where(table.c.file_name == source_name)
        delete_count = session.execute(stmt).rowcount

    for _, row in df.iterrows():
        row_dict = row.to_dict()

        stmt = insert(table).values(**row_dict)
        session.execute(stmt)

    log.info(f'Таблица {table.name}: внесено - {len(df)} удалено старых записей - {delete_count}')


def upload_to_mysql(
    df: pd.DataFrame,
    category: str,
    source_name: Optional[str] = None
) -> None:
    """Отправка данных мониторинга в базу данных MySQL.

    Заменяет значения NaN на None и загружает DataFrame
    в соответствующую таблицу категории.

    Args:
        df: датафрейм с данными мониторинга для загрузки
        category: категория мониторинга для определения целевой таблицы
        source_name: имя исходного файла

    Returns:
        None
    """
    df = df.replace({float('nan'): None})
    df = df.where(pd.notnull(df), None)

    db_table_raw = raw_tables[category]
    table_raw = db_manager.safe_reflection(db_table_raw)

    upload_table(df=df, table=table_raw, source_name=source_name)


@manage_sessions()
def get_historical_data(
        session: Session,
        category: str,
        columns: List[str],
        date_from: datetime,
        date_to: Optional[datetime] = None
) -> pd.DataFrame:
    """Получение исторических данных мониторинга из базы данных.

    Извлекает данные из таблицы указанной категории с возможностью
    фильтрации по дате и выбора конкретных столбцов.

    Args:
        session: сессия базы данных, предоставляемая декоратором manage_sessions
        category: категория мониторинга для определения целевой таблицы
        columns: список имён столбцов для извлечения
        date_from: начальная дата для фильтрации данных (включительно)
        date_to: конечная дата для фильтрации данных (включительно), если не указана, используется текущая дата

    Returns:
        DataFrame с историческими данными мониторинга, индексированный по id
    """
    if not date_to:
        date_to = datetime.now()
    table = db_manager.safe_reflection(raw_tables[category])

    stmt = select(
        table.c[*columns]
    ).where(
        (table.c.date >= date_from) & (table.c.date <= date_to)
    )

    df = pd.read_sql(stmt, session.bind, index_col='id')
    return df


@manage_sessions()
def update_table_data_by_id(
    session: Session,
    category: str,
    df: Tuple[pd.DataFrame, pd.Series]
) -> None:
    """Обновление данных в таблице базы данных по идентификатору.

    Выполняет пакетное обновление записей в таблице указанной категории.
    Индексы DataFrame используются как значения id для поиска записей в БД.

    Args:
        session: сессия базы данных, предоставляемая декоратором manage_sessions
        category: категория мониторинга для определения целевой таблицы
        df: DataFrame или Series с данными для обновления; индексы используются
            как идентификаторы записей

    Returns:
        None
    """
    table = db_manager.safe_reflection(raw_tables[category])

    if isinstance(df, pd.Series):
        df = df.to_frame()

    df_bulk = df.rename_axis("b_id").reset_index()
    params = df_bulk.to_dict(orient="records")

    stmt = update(table).where(table.c.id == bindparam("b_id"))
    session.execute(stmt, params)
