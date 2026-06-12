"""
Функции для получения данных из бд

@author Sergey Vakhrameev
"""
import lib.db as ldb


def non_opening_users():
    """
    Получение неоткрывающих рассылку пользователей
    """
    database = ldb.create_connect_db_m16()
    cursor = database.cursor()

    query = "SELECT * FROM emailer.email_maillist WHERE maillist_id = %s"
    cursor.execute(query, (191815,))
    items = cursor.fetchall()

    cursor.close()
    database.close()

    return items

def unsubscribed_from_mailing_users(axe_id):
    """
    Получение отписавшихся от рассылки пользователей
    """
    database = ldb.create_connect_db_m16()
    cursor = database.cursor()

    query = "SELECT * FROM emailer.email_maillist WHERE maillist_id = %s"
    cursor.execute(query, (axe_id,))
    items = cursor.fetchall()

    cursor.close()
    database.close()

    return items


def user_mailing_activities(number_of_days, site='meatinfo'):
    """
    Получение таблицы со статистикой по открытиям рассылок
    """
    client = ldb.create_client_ch()

    sql = f"""
        SELECT up.login email,
            t2.userId,
            t2.itemId axeId,
            sent,
            open,
            date_sent,
            date_open
        FROM (
                SELECT t.userId,
                        sum(sent) sent,
                        sum(open) open,
                        t.itemId,
                        max(date_sent) date_sent,
                        if(open > 0, max(date_open), null) date_open
                FROM (
                        SELECT us.userId,
                                JSONExtractInt(us.data, 'messageId') messageId,
                                countIf(us.type = 'email_sent') > 0  sent,
                                countIf(us.type = 'email_open') > 0  open,
                                us.itemId,
                                maxIf(us.dateEvent, us.type = 'email_sent') date_sent,
                                if(open > 0, maxIf(us.dateEvent, us.type = 'email_open'), null) date_open
                        FROM axe.userStat us
                        WHERE us.type in ('email_sent', 'email_open')
                            AND us.site = '{site}'
                            AND us.dateEvent > now() - INTERVAL {number_of_days} day
                        GROUP BY us.userId, us.itemId, messageId
                        ) t
                GROUP BY t.userId, t.itemId
            ) t2
                JOIN axe.userProfile up ON up.userId = t2.userId
            WHERE up.site = '{site}';
    """

    items = client.execute(sql)

    return items
