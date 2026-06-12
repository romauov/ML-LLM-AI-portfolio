"""
Запросы к базе данных clickhouse

@author Sergey Goncharov
"""
import dateparser

from lib.db import create_client_ch

exclusion_users = [2, 7, 10, 14903, 16005, 34272, 36832, 55508, 55678, 56709, 81860, 94154, 96104, 99194,
                   101444, 104849, 135786, 144792, 166055, 171344, 172753, 204902, 207281, 211701, 212080,
                   224268, 225329, 233862, 234008, 239509, 253278, 254481, 258944, 259162, 259654, 260854,
                   260961, 261124, 261198, 261527, 261870, 262575, 263064, 263659, 263668, 263744, 264599,
                   266938, 267284]


def user_views_service(months_ago: int, interval: int) -> list:
    """
    Статистика пользователей для датасета
    :param interval: количество месяцев интервалов
    :param months_ago: количество месяцев всего периода
    :return:
    """
    date_start = dateparser.parse(f'{months_ago} months ago').strftime("%Y-%m-%d")
    date_end = dateparser.parse(f'{months_ago - interval} months ago').strftime("%Y-%m-%d")
    client = create_client_ch()

    sql = """
    SELECT t.*,
           up.position,
           up.activity
        FROM (
    SELECT us.userId,
           countIf(us.type = 'create_buy') createBuy,
           countIf(us.type = 'create_sale') createSale,
           countIf(us.type = 'create_up_buy') createUpBuy,
           countIf(us.type = 'create_up_sale') createUpSale,
           countIf(us.type = 'edit_up_buy') editUpBuy,
           countIf(us.type = 'edit_up_sale') editUpSale,
           countIf(us.type = 'watch_sale') watchSale,
           countIf(us.type = 'watch_buy') watchBuy,
           countIf(us.type = 'activity_trade') activityTrade,
           countIf(us.type = 'activity_company') activityCompany,
           countIf(us.type = 'activity_profile') activityProfile,
           countIf(us.type = 'my_offers') myOffers,
           countIf(us.type = 'profile_view') profileView,
           countIf(us.type = 'trade_photo_view') tradePhotoView,
           countIf(us.type = 'trade_to_profile_view') tradeToProfileView,
           countIf(us.type = 'trade-filter') tradeFilter,
           countIf(us.type = 'message') message,
           countIf(us.type = 'company_view') viewCompany,
           countIf(us.type = 'monitoring_view') monitoringView,
           countIf(us.type = 'news_view') newsView,
           countIf(us.type = 'analytics_view') analyticsView,
           countIf(us.type = 'dynamics_view') dynamicsView,
           countIf(us.type = 'view_shop') viewShop,
           countIf(DISTINCT us.itemId, us.type = 'view_shop') viewShopUniq,
           toString(groupUniqArrayIf(us.itemId, us.type = 'view_shop')) viewShopList,
           countIf(us.type = 'add_shop') addShop,
           toString(groupUniqArrayIf(us.itemId, us.type = 'add_shop')) addShopList,
           countIf(us.type = 'pay_shop') payShop,
           toString(groupUniqArrayIf(us.itemId, us.type = 'pay_shop')) payShopList
    FROM userStat us
             JOIN (SELECT userId
                   FROM userStat
                   WHERE type = 'view_shop'
                     AND site = 'meatinfo'
                     AND datetimeEvent >= %(start)s
                     AND datetimeEvent < %(end)s
                     AND userId not in %(exclusion_users)s
                   GROUP BY userId) user_vs ON user_vs.userId = us.userId
    WHERE us.site = 'meatinfo'
      AND datetimeEvent >= %(start)s
      AND datetimeEvent < %(end)s
    GROUP BY us.userId
    ORDER BY payShop DESC, viewShop DESC
    ) t
    JOIN userProfile up ON up.userId = t.userId
    WHERE up.site = 'meatinfo';
    """

    print(date_start, date_end)

    items = client.execute(sql, {
        'start': date_start,
        'end': date_end,
        'exclusion_users': exclusion_users
    })

    return items


def users_stat(users: list, months_ago: int) -> list:
    """
    Статистика пользователей для работы модели
    :param users: id пользователей
    :param months_ago: количество месяцев периода
    :return:
    """
    date_start = dateparser.parse(f'{months_ago} months ago').strftime("%Y-%m-%d")
    client = create_client_ch()

    sql = """
        SELECT countIf(us.type = 'create_buy') createBuy,
               countIf(us.type = 'create_sale') createSale,
               countIf(us.type = 'create_up_buy') createUpBuy,
               countIf(us.type = 'create_up_sale') createUpSale,
               countIf(us.type = 'edit_up_buy') editUpBuy,
               countIf(us.type = 'edit_up_sale') editUpSale,
               countIf(us.type = 'watch_sale') watchSale,
               countIf(us.type = 'watch_buy') watchBuy,
               countIf(us.type = 'activity_trade') activityTrade,
               countIf(us.type = 'activity_company') activityCompany,
               countIf(us.type = 'activity_profile') activityProfile,
               countIf(us.type = 'my_offers') myOffers,
               countIf(us.type = 'profile_view') profileView,
               countIf(us.type = 'trade_photo_view') tradePhotoView,
               countIf(us.type = 'trade_to_profile_view') tradeToProfileView,
               countIf(us.type = 'trade-filter') tradeFilter,
               countIf(us.type = 'message') message,
               countIf(us.type = 'company_view') viewCompany,
               countIf(us.type = 'monitoring_view') monitoringView,
               countIf(us.type = 'news_view') newsView,
               countIf(us.type = 'analytics_view') analyticsView,
               countIf(us.type = 'dynamics_view') dynamicsView,
               countIf(us.type = 'view_shop') viewShop,
               countIf(DISTINCT us.itemId, us.type = 'view_shop') viewShopUniq
        FROM userStat us
                 JOIN (SELECT userId
                       FROM userStat
                       WHERE type = 'view_shop'
                         AND site = 'meatinfo'
                         AND datetimeEvent > %(start)s
                         AND userId in %(users)s
                       GROUP BY userId) user_vs ON user_vs.userId = us.userId
        WHERE us.site = 'meatinfo'
          AND datetimeEvent > %(start)s
        GROUP BY us.userId
        """

    items = client.execute(sql, {
        'start': date_start,
        'users': users
    })

    return items


def active_users(activity: int) -> list:
    """
    Список активных пользователей
    :param activity: Активность недель
    """
    sql = """
    SELECT u.userId,
       up.firstname,
       up.lastname,
       up.login,
       date
    FROM (
         SELECT userId, max(dateEvent) date
         FROM userStat
         WHERE dateEvent > NOW() - INTERVAL %(activity)s WEEK
           AND site = 'meatinfo'
           AND userId not in %(exclusion_users)s
         GROUP BY userId
         ) u
         JOIN userProfile up ON up.userId = u.userId
         LEFT JOIN (
            SELECT userId uid
            FROM userStat
            WHERE type = 'pay_shop' AND site = 'meatinfo'
            GROUP BY uid
         ) pay ON pay.uid = u.userId
    WHERE up.site = 'meatinfo' AND pay.uid = 0
    ORDER BY date DESC;
    """

    client = create_client_ch()
    items = client.execute(sql, {
        'activity': activity,
        'exclusion_users': exclusion_users
    })

    return items
