"""
Скрипт для управлениями сессиями SQLAlchemy

@author Sergei Romanov
"""
import time
from functools import wraps

import pymysql
from sqlalchemy import MetaData, Table, create_engine
from sqlalchemy.exc import DisconnectionError, OperationalError
from sqlalchemy.orm import scoped_session, sessionmaker

from app.utils.logger import logger as log
from app.utils.settings import secrets as s

sql_err_codes = (2006, 2013, 2014, 2045, 2055)


def check_reset_confition(e):
    condition = hasattr(e, 'orig') and isinstance(
        e.orig, pymysql.err.OperationalError) and e.orig.args[0] in sql_err_codes
    return condition


class DBManager():
    def __init__(self):
        self.engine = None
        self.Session = None
        self.reset_engine()

    def reset_engine(self):
        """Полностью пересоздает движок и фабрику сессий"""

        # Закрываем текущий движок
        if self.engine:
            log.warning("Database engine restarts")
            self.engine.dispose()

        # Создаем новый движок
        self.engine = create_engine(
            f'mysql+pymysql://{s.db_user}:{s.db_password}@{s.db_host}:{s.db_port}/{s.db_name}',
            pool_recycle=3600,  # Пересоздавать соединения каждый час
            pool_pre_ping=True   # Проверять соединение перед использованием
        )
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        # log.warning("Database engine initialized")

    def safe_reflection(self, table_name, retries=5, delay=60):
        """Безопасное отражение таблицы с обработкой ошибок соединения"""
        attempt = 0
        metadata = MetaData()

        while attempt < retries:
            try:
                return Table(
                    table_name,
                    metadata,
                    autoload_with=self.engine,
                    extend_existing=True
                )
            except (OperationalError, DisconnectionError) as e:
                if check_reset_confition(e):
                    log.error(f"Connection error during table reflection: {e}")
                    self.reset_engine()
                    attempt += 1
                    time.sleep(delay * attempt)
                else:
                    raise

        raise OperationalError(
            f"Table reflection failed after {retries} attempts")


db_manager = DBManager()


def manage_sessions(retries=5, delay=60, recreate_engine_codes=sql_err_codes):
    """
    Улучшенный декоратор с пересозданием движка при критических сбоях

    Args:
        retries: Количество попыток выполнения
        delay: Задержка между попытками (секунды)
        recreate_engine_codes: Коды ошибок, требующие пересоздания движка
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal retries, delay
            attempt = 0

            while attempt < retries:
                session = db_manager.Session()
                try:
                    result = func(session, *args, **kwargs)
                    session.commit()
                    return result

                except (OperationalError, DisconnectionError) as e:
                    session.rollback()
                    log.error(f"Database error in {func.__name__}: {str(e)}")

                    # Проверяем необходимость пересоздания движка
                    if check_reset_confition(e):
                        log.critical(
                            "Critical connection error. Recreating engine...")
                        db_manager.reset_engine()

                    attempt += 1
                    if attempt < retries:
                        # Экспоненциальная задержка
                        time.sleep(delay * attempt)

                except Exception as e:
                    session.rollback()
                    log.error(f"General error in {func.__name__}: {str(e)}")
                    attempt += 1
                    if attempt < retries:
                        time.sleep(delay)

                finally:
                    session.close()

            raise RuntimeError(
                f"Function {func.__name__} failed after {retries} attempts")
        return wrapper
    return decorator
