"""
Выгрузка профилей meatinfo и fishretail, названий регионов и информации о компании

@author Sergei Romanov
"""
import pandas as pd
# pylint: disable=import-error
from user_card import \
    COMPANY_COLUMNS, EMAILS_COLUMNS, MEAT_FISH_COLUMNS, REGION_COLUMNS, TRADEBOARD_COLUMNS, USERSTAT_COLUMNS
from .db import create_client_ch, create_connect_db_m16_stage

ADMIN_USERS = (2, 7, 10, 14903, 16005, 34272, 36832, 55508, 55678, 56709, 81860, 94154, 96104,
               99194, 101444, 104849, 135786, 144792, 166055, 171344, 172753, 204902, 207281, 211701, 212080,
               224268, 225329, 233862, 234008, 239509, 253278, 254481, 258944, 259162, 259654, 260854, 260961,
               261124, 261198, 261527, 261870, 262575, 263064, 263659, 263668, 263744, 264599, 266938, 267284)

def create_company(cursor):
    """Выгрузка данных по компаниям
    Args:
        cursor: create_connect_db_m16_stage().cursor()
        
    Returns:
        данные по компаниям
    """
    query = """
            SELECT id, name_ru, url, company_inn, director_ru, image_id, description_ru
            FROM catalogue.company
            """
    cursor.execute(query)
    data = cursor.fetchall()
    return data

def create_fishretail(cursor):
    """Выгрузка данных пользователя с таблицы fishretail
    Args:
        cursor: create_connect_db_m16_stage().cursor()
        
    Returns:
        данные из профиля fishretail
    """
    query = """
    SELECT user_id, firstname, lastname, company_id, position, activity, 
    phone, phone_privacy, mobilephone, mobilephone_privacy, 
    site, icq, gtalk, skype, viber, whats_app, telegram
    FROM fishretail.user_profile
    """

    cursor.execute(query)
    data = cursor.fetchall()
    return data


def create_meatinfo(cursor):
    """Выгрузка данных пользователя с таблицы meatinfo
    Args:
        cursor: create_connect_db_m16_stage().cursor()
        
    Returns:
        данные из профиля meatinfo
    """
    sql = """
    SELECT user_id, firstname, lastname, company_id, position, activity, 
    phone, phone_privacy, mobilephone, mobilephone_privacy, 
    site, icq, gtalk, skype, viber, whats_app, telegram
    FROM meatinfo.user_profile
    """

    cursor.execute(sql)
    data = cursor.fetchall()
    return data

def create_regions(cursor):
    """Выгрузка названий регионов
    Args:
        cursor: create_connect_db_m16_stage().cursor()
        
    Returns:
        названия регионов
    """
    query = """
            SELECT id, name
            FROM geobaza.region
            """
    cursor.execute(query)
    data = cursor.fetchall()
    return data

def create_pipeline():
    """папйлан выгрузки данных
    
    Returns:
        данные из Adminer
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()

    company = create_company(cursor)
    fish = create_fishretail(cursor)
    meat = create_meatinfo(cursor)
    regions = create_meatinfo(cursor)

    cursor.close()

    return company, fish, meat, regions

def make_company_sql(cursor, company_id):
    """Выгрузка данных по компании
    Args:
        cursor: create_connect_db_m16_stage().cursor()
        company_id (int): id компании
        
    Returns:
        данных по компании
    """
    query =  f"""
            SELECT id, name_ru, url, company_inn, director_ru, image_id, description_ru
            FROM catalogue.company
            WHERE id = {company_id}
            """
    cursor.execute(query)
    data = cursor.fetchall()
    return data

def make_email_sql(client, userid, site):
    """Выгрузка эл.почты пользователя
    Args:
        client: create_client_ch(),
        userid (int): id пользователя,
        site (str): fishretail или meatinfo
        
    Returns:
        эл.почта пользователя
    """
    query = f"""SELECT userId,
                 login,
                 site
          FROM axe.userProfile up
          WHERE site = '{site}' AND userId = {userid}
          """
    data = client.execute(query)
    return data

def make_fish_sql(cursor, userid):
    """Выгрузка данных из профиля fishretail
    Args:
        cursor: create_connect_db_m16_stage().cursor()
        userid (int): id профиля
        
    Returns:
        данные пользователя
    """
    if isinstance(userid, int):
        condition = f'WHERE user_id in ({userid})'
    else:
        condition = f'WHERE user_id in ({", ".join(str(i) for i in userid)})'
    query =  f"""
    SELECT user_id, firstname, lastname, company_id, position, activity, 
    phone, phone_privacy, mobilephone, mobilephone_privacy, 
    site, icq, gtalk, skype, viber, whats_app, telegram
    FROM fishretail.user_profile
    {condition}
    """
    cursor.execute(query)
    data = cursor.fetchall()
    return data

def make_meat_sql(cursor, userid):
    """Выгрузка данных из профиля meatinfo
    Args:
        cursor: create_connect_db_m16_stage().cursor()
        userid (int): id профиля
        
    Returns:
        данные пользователя
    """
    if isinstance(userid, int):
        condition = f'WHERE user_id in ({userid})'
    else:
        condition = f'WHERE user_id in ({", ".join(str(i) for i in userid)})'
    query =  f"""
    SELECT user_id, firstname, lastname, company_id, position, activity, 
    phone, phone_privacy, mobilephone, mobilephone_privacy, 
    site, icq, gtalk, skype, viber, whats_app, telegram
    FROM meatinfo.user_profile
    {condition}
    """
    cursor.execute(query)
    data = cursor.fetchall()
    return data

def make_tradeboard_sql(client, userid, site):
    """Выгрузка объявлений пользователя
    Args:
        client: create_client_ch(),
        userid (int): id пользователя,
        site (str): fishretail или meatinfo
        
    Returns:
        данные с объявлениями пользователя
    """
    query = f"""
           SELECT *
           FROM axe.tradeboard t
           WHERE site in '{site}'
           AND userId = {userid}
           """
    data = client.execute(query)

    return data

def make_regions_sql(cursor):
    """Выгрузка названий регионов
    Args:
        cursor: create_connect_db_m16_stage().cursor()
        
    Returns:
        названия регионов
    """
    query = """
            SELECT id, name
            FROM geobaza.region
            """
    cursor.execute(query)
    data = cursor.fetchall()
    return data

def make_userstat_sql(client, userid, site, trades=None, number_of_months=12):
    """Выгрузка названий регионов
    Args:
        client: create_client_ch(),
        userid (int): id профиля,
        site (str): fishretail или meatinfo,
        trades (lst): список объявлений. Defaults to None,
        number_of_months (int): временной период для выгрузки данных
        
    Returns:
        данные действий пользователя
    """
    if trades is None:
        condition = f"""
        WHERE us.site = '{site}'
        AND us.userId = {userid}
        AND us.datetimeEvent > now() - INTERVAL {number_of_months} month
        """
        extra_condition = f"""
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
            {condition}
            
            AND us.type = 'search'
            ORDER BY us.datetimeEvent
    """
    else:
        trades = f'({", ".join(str(trade) for trade in trades)})'
        condition = f"""
        WHERE us.site = '{site}'
        AND us.userId != {userid}
        AND us.userId NOT in {ADMIN_USERS}
        AND offerId in {trades}
        """
        extra_condition = ''

    query = f"""
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
            {condition}
            
            AND us.type in (
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
                'my_offers','order_from_trade',
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
            SELECT us.userId,us.site,
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
            {condition}
            
            AND us.type = 'message'
            AND JSONExtractString(data, 'type') = 'trade'
            ORDER BY us.datetimeEvent
            
            {extra_condition}
            
            ) t
        ORDER BY t.date;
    """

    data = client.execute(query)

    return data
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
def make_pipeline(site, userid):
    """выгрузка данных и создание датасетов

    Args:
        site (str): fishretail или meatinfo
        userid (int): id пользоателя

    Returns:
        набор датасетов
    """
    client = create_client_ch()
    db = create_connect_db_m16_stage()
    cursor = db.cursor()
    #userstat c сдействиями пользователя
    stats = pd.DataFrame(make_userstat_sql(client, userid, site), columns=USERSTAT_COLUMNS)
    #tradeboard объявлениями пользователя
    trade_df = pd.DataFrame(make_tradeboard_sql(client, userid, site), columns=TRADEBOARD_COLUMNS)

    if site == 'meatinfo':
        profile = make_meat_sql(cursor, userid)
    else:
        profile = make_fish_sql(cursor, userid)
    #датафрейм с данными пользователя
    profile_df = pd.DataFrame(profile, columns=MEAT_FISH_COLUMNS)
    try:
        company_id = profile_df['company_id'].values[0]
    except IndexError:
        company_id = None
    #датафрейм с информацией о компании пользователя
    if company_id:
        company_df = pd.DataFrame(make_company_sql(cursor, company_id), columns=COMPANY_COLUMNS)
    else:
        company_df = None
    #оъявления пользователя
    user_trades = trade_df['itemId'].unique()
    #действия с объявлениями полььзователя
    if len(user_trades) > 0:
        stats_to = pd.DataFrame(make_userstat_sql(client, userid, site, user_trades), columns=USERSTAT_COLUMNS)
    else:
        stats_to = None
    #датафрейм с названиями регионов
    regions = pd.DataFrame(make_regions_sql(cursor), columns=REGION_COLUMNS)
    #датафрйем с эл.почтой пользовате6ля
    emails = pd.DataFrame(make_email_sql(client, userid, site), columns=EMAILS_COLUMNS)

    if stats_to is None:
        lead_df = None
        watch_df = None
    else:
        lead_actions = ['message', 'callButtonTrade', 'comment_trade',
                    'order_from_trade', 'activity_trade', 'activity_profile']
        lead_ids = stats_to.loc[stats_to['type'].isin(lead_actions)]['userId'].unique()
        if len(lead_ids) == 0:
            lead_df = None
        else:
            if site == 'meatinfo':
                lead_names = make_meat_sql(cursor, lead_ids)
            else:
                lead_names= make_fish_sql(cursor, lead_ids)
            #датафрейм с именами пользователей, обращавшихся к объявленим
            lead_df = pd.DataFrame(lead_names, columns=MEAT_FISH_COLUMNS)

        search_actions = ['watch_sale', 'watch_buy', 'watch_else', 'trade_to_profile_view', 'trade_photo_view']
        watch_ids = stats_to.loc[stats_to['type'].isin(search_actions)]['userId'].unique()
        if len(watch_ids) == 0:
            watch_df = None
        else:
            if site == 'meatinfo':
                watch_names = make_meat_sql(cursor, watch_ids)
            else:
                watch_names= make_fish_sql(cursor, watch_ids)
            #датафрейм с имена пользователей, просматривавших объявления
            watch_df = pd.DataFrame(watch_names, columns=MEAT_FISH_COLUMNS)

    cursor.close()

    return company_df, emails, lead_df, profile_df, regions, stats, stats_to, trade_df, watch_df
