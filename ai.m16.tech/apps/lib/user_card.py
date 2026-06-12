"""
Выгрузка профилей meatinfo и fishretail, названий регионов и информации о компании

@author Sergei Romanov
"""

from .db import create_client_ch, create_connect_db_m16_stage

ADMIN_USERS = (2, 7, 10, 14903, 16005, 34272, 36832, 55508, 55678, 56709, 81860, 94154, 96104,
               99194, 101444, 104849, 135786, 144792, 166055, 171344, 172753, 204902, 207281, 211701, 212080,
               224268, 225329, 233862, 234008, 239509, 253278, 254481, 258944, 259162, 259654, 260854, 260961,
               261124, 261198, 261527, 261870, 262575, 263064, 263659, 263668, 263744, 264599, 266938, 267284)

def create_add_date():
    """Выгрузка данных с датой регистрации пользователя
    """
    client = create_client_ch()
    query = """
    SELECT userId, site, dateAdd
    FROM userProfile
    WHERE site in ('meatinfo', 'fishretail')
    """
    items = client.execute(query)
    return items

def create_company():
    """Выгрузка данных по компаниям
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()
    query = """
            SELECT id, name_ru, url, company_inn, director_ru, image_id, description_ru
            FROM catalogue.company
            """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data

def create_fishretail():
    """Выгрузка данных пользователя с таблицы fishretail

    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()

    query = """
    SELECT user_id, firstname, lastname, company_id, position, activity, 
    phone, phone_privacy, mobilephone, mobilephone_privacy, 
    site, icq, gtalk, skype, viber, whats_app, telegram, date_modify
    FROM fishretail.user_profile
    """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data

def create_last_date():
    """Выгрузка данных о последней активности пользователя
    """
    client = create_client_ch()
    query = """
    SELECT userId, site, MAX(datetimeEvent) AS last_date
    FROM userStat
    WHERE site in ('meatinfo', 'fishretail')
    GROUP BY userId, site
    """
    items = client.execute(query)
    return items

def create_meatinfo():
    """Выгрузка данных пользователя с таблицы meatinfo
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()
    query = """
    SELECT user_id, firstname, lastname, company_id, position, activity, 
    phone, phone_privacy, mobilephone, mobilephone_privacy, 
    site, icq, gtalk, skype, viber, whats_app, telegram, date_modify
    FROM meatinfo.user_profile
    """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data

def create_regions():
    """Выгрузка названий регионов
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()
    query = """
            SELECT id, name
            FROM geobaza.region
            """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data

def create_user_stat(number_of_months=12, site=('meatinfo', 'fishretail')):
    """
    Получение таблицы user_stat
    """
    client = create_client_ch()

    sql = f"""
        SELECT *
        FROM (
                 SELECT us.userId,
                        us.site,
                        up.regionId      userRegion,
                        us.type,
                        t.itemId         offerId,
                        toString(t.dealType),
                        t.type1,
                        t.type2,
                        t.regionId       offerRegion,
                        us.datetimeEvent date
                 FROM userStat us
                          JOIN tradeboard t ON t.itemId = us.itemId AND t.site = us.site
                          JOIN userProfile up ON up.userId = us.userId AND up.site = us.site
                 WHERE us.site in {site}
                   AND us.datetimeEvent > now() - INTERVAL {number_of_months} month
                   AND us.type in
                       (
                'activity_profile',
                'activity_trade',
                'callButtonTrade',
                'comment_trade',
                'create_buy',
                'create_else',
                'create_sale',
                'create_up_buy',
                'create_up_else',
                'create_up_sale',
                'edit_up_buy',
                'edit_up_else',
                'edit_up_sale',
                'message',
                'my_offers',
                'order_from_trade',
                'search',
                'watch_buy',
                'watch_else',
                'watch_sale',
                'trade_photo_view'
                )
                   AND t.type1 is not null
                   AND t.dealType IS NOT NULL
                 ORDER BY us.datetimeEvent
                     UNION ALL
                 SELECT us.userId,
                        us.site,
                        up.regionId      userRegion,
                        us.type,
                        t.itemId         offerId,
                        toString(t.dealType),
                        t.type1,
                        t.type2,
                        t.regionId       offerRegion,
                        us.datetimeEvent date
                 FROM userStat us
                     JOIN tradeboard t
                 ON t.itemId = toUInt32OrNull(JSONExtractString(us.data, 'tradeId')) AND t.site = us.site
                     JOIN userProfile up ON up.userId = us.userId AND up.site = us.site
                 WHERE us.site in {site}
                   AND us.datetimeEvent > now() - INTERVAL {number_of_months} month
                   AND us.type = 'message'
                   AND JSONExtractString(data, 'type') = 'trade'
                 ORDER BY us.datetimeEvent
                 UNION ALL
                 SELECT us.userId,
                     us.site,
                     up.regionId                            userRegion,
                     us.type,
                     0                                      itemId,
                     JSONExtractString(us.data, 'dealType') dealType,
                     JSONExtractString(us.data, 'query')    type1,
                     ''                                     type2,
                     JSONExtractInt(us.data, 'regionId')    offerRegion,
                     us.datetimeEvent                       date
                 FROM userStat us
                     JOIN userProfile up ON up.userId = us.userId AND up.site = us.site
                 WHERE us.site in {site}
                   AND us.datetimeEvent > now() - INTERVAL {number_of_months} month
                   AND us.type = 'search'
                 ORDER BY us.datetimeEvent
             ) t
        ORDER BY t.date;
    """

    items = client.execute(sql)

    return items
