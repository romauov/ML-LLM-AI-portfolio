"""
Подключение к базе данных

@author Sergey Goncharov
"""
import os

from clickhouse_driver import Client
from mysql.connector import connect

# Production
DB_M16_HOST = os.getenv('DB_M16_HOST', 'localhost')
# Stage
DB_M16_HOST_STAGE = os.getenv('DB_M16_HOST_STAGE', 'localhost')
DB_AXE_HOST = os.getenv('DB_AXE_HOST', 'localhost')
DB_CH_HOST = os.getenv('DB_CH_HOST', 'localhost')
DB_M16_PORT = int(os.getenv('DB_M16_PORT', '3306'))
DB_AXE_PORT = int(os.getenv('DB_AXE_PORT', '3402'))
DB_CH_PORT = int(os.getenv('DB_CH_PORT', '9096'))

if os.environ['MODE'] == 'DEV':
    DB_M16_HOST = 'localhost'
    DB_AXE_HOST = 'localhost'
    DB_CH_HOST = 'localhost'
    DB_M16_PORT = 3307
    DB_AXE_PORT = 3306
    DB_CH_PORT = 9000


def create_connect_db_m16():
    """
    Соединение с базой m16

    Пример:
    db = create_connect_db_m16()
    cursor = db.cursor()
    query = "SELECT * FROM table WHERE id = %s"
    cursor.execute(query, (123,))
    items = cursor.fetchall()
    cursor.close()
    cnx.close()
    """
    return connect(host=DB_M16_HOST, user=os.getenv('DB_M16_USER', 'axe'), password=os.getenv('DB_M16_PASSWORD', 'axe'), port=DB_M16_PORT)

def create_connect_db_m16_stage():
    """
    Соединение с базой m16 на stage
    """
    return connect(host=DB_M16_HOST_STAGE, user=os.getenv('DB_M16_USER', 'axe'), password=os.getenv('DB_M16_PASSWORD', 'axe'), port=DB_M16_PORT)


def create_connect_db_axe():
    """
    Соединение с базой axe
    """
    return connect(host=DB_AXE_HOST, user=os.getenv('DB_AXE_USER', 'ai_m16'), password=os.getenv('DB_AXE_PASSWORD', ''), port=DB_AXE_PORT)


def create_client_ch():
    """
    Соединение с базой clickhouse
    """

    client = Client(host=DB_CH_HOST, port=DB_CH_PORT, user=os.getenv('DB_CH_USER', 'ai_m16'), password=os.getenv('DB_CH_PASSWORD', ''), database='axe')

    return client
