"""
Выгрузка tradeboard по мясу и рыбе из clickhouse

@author Dmitry Abramov
"""
from .db import create_client_ch


def clickhouse_tradeboard():
    """
    Получение таблицы user_stat
    """
    client = create_client_ch()

    sql =  """
           SELECT *
           FROM axe.tradeboard t
           WHERE site in ('fishretail', 'meatinfo')
           """

    items = client.execute(sql)

    return items
