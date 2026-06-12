import random
import time
import traceback

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.schemas import ClientData
from utils.logger import logger as log
from utils.settings import secrets as s


def get_client_data_from_db():
    max_attempts = 5
    base_delay = 30
    clients = []

    for attempt in range(max_attempts):
        try:
            engine = create_engine(
                f'mysql+pymysql://{s.db_user}:{s.db_password}@{s.db_host}/{s.db_name}',
                pool_pre_ping=True
            )
            query = """SELECT client_name, table_id, sheet_id, price_id, price_sheet, channel_id, token, manager_ids
            FROM axe_bot
            WHERE deleted = 0"""

            with engine.connect() as conn:
                result = conn.execute(text(query)).fetchall()

            for row in result:
                manager_ids_str = row.manager_ids
                if manager_ids_str:
                    manager_ids = [int(id_str)
                                   for id_str in manager_ids_str.split(',')]
                else:
                    manager_ids = []

                client_data = {
                    "client_name": row.client_name,
                    "table_id": row.table_id,
                    "sheet_id": row.sheet_id,
                    "price_id": row.price_id if row.price_id else None,
                    "price_sheet": row.price_sheet if row.price_sheet else None,
                    "channel_id": row.channel_id,
                    "token": row.token,
                    "manager_ids": manager_ids
                }

                try:
                    client = ClientData(**client_data)
                    clients.append(client)
                except Exception as e:
                    log.error(f"Failed to create client '{client_data.get('client_name')}': {e}")
                    log.error(traceback.format_exc())

            return clients  # Успешное выполнение - возвращаем результат

        except OperationalError as e:
            log.error(
                f"Database connection error (attempt {attempt + 1}/{max_attempts}): {e}")
            log.error(traceback.format_exc())
            if attempt < max_attempts - 1:

                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                log.warning(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                raise ConnectionError(
                    "Failed to connect to database after 5 attempts") from e

        except Exception as e:
            log.error(f"Unexpected error during database operation: {e}")
            log.error(traceback.format_exc())
            raise
