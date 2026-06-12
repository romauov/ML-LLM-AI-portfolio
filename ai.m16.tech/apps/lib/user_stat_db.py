"""
Функции для получения данных из бд

@author Sergey Vakhrameev
"""
from .db import create_client_ch


def user_stat(number_of_months=12, site=('meatinfo', 'fishretail')):
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
                       ('watch_buy', 'watch_else', 'watch_sale',
                        'create_buy', 'create_else', 'create_sale',
                        'create_up_buy', 'create_up_else', 'create_up_sale', 'edit_up_buy',
                        'edit_up_else', 'edit_up_sale',
                        'my_offers', 'activity_trade', 'comment_trade', 'trade_photo_view', 'order_from_trade',
                        'callButtonTrade')
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

def email_db():
    """
    Получение списка email пользователей
    """
    client = create_client_ch()

    sql = """
          SELECT userId,
                 login email,
                 site
          FROM axe.userProfile up
          WHERE site in ('meatinfo', 'fishretail')
    """

    items = client.execute(sql)

    return items
