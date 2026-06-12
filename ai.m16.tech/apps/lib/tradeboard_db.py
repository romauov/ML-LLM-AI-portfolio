"""
Выгрузка текстов объявлений

@author Marat Ibatullin
"""

from .db import create_connect_db_m16_stage

def tradeboard_meatinfo():
    """
    Выгрузка текстов объявлений с meatinfo

    Возвращает таблицу с текстами и названиями обновлений для 
    последующего вычисления эмбеддингов
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()
    query = """
            SELECT id,
                   user_id,
                   title,
                   descr,
                   city_id,
                   region_id,
                   human_url_alias
            FROM meatinfo.tradeboard
            """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data

def tradeboard_fishretail():
    """
    Выгрузка текстов объявлений с fishretail

    Возвращает таблицу с текстами и названиями обновлений для 
    последующего вычисления эмбеддингов
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()
    query = """
            SELECT id,
                   user_id,
                   title,
                   descr,
                   city_id,
                   region_id,
                   human_url_alias
            FROM fishretail.tradeboard
            """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data
