"""
Запросы к базе данных
@author Sergey Goncharov
"""

from lib.db import create_client_ch


def user_mailing_activities():
    """
        Выгрузка просмотра пользователями рассылок
    """

    client = create_client_ch()

    sql = """
        SELECT up.login email,
           t2.userId,
           sent,
           open,
           date_sent,
           date_open
        FROM (
                 SELECT t.userId,
                        sum(sent) sent,
                        sum(open) open,
                        max(date_sent) date_sent,
                        if(open > 0, max(date_open), null) date_open
                 FROM (
                          SELECT us.userId,
                                 JSONExtractInt(us.data, 'messageId') messageId,
                                 countIf(us.type = 'email_sent') > 0  sent,
                                 countIf(us.type = 'email_open') > 0  open,
                                 maxIf(us.dateEvent, us.type = 'email_sent') date_sent,
                                 if(open > 0, maxIf(us.dateEvent, us.type = 'email_open'), null) date_open
                          FROM axe.userStat us
                          WHERE us.type in ('email_sent', 'email_open')
                            AND us.site = 'meatinfo'
                            AND us.dateEvent > now() - INTERVAL 12 month
                          GROUP BY us.userId, messageId
                          ) t
                 GROUP BY t.userId
             ) t2
                 JOIN axe.userProfile up ON up.userId = t2.userId
            WHERE up.site = 'meatinfo';
    """

    items = client.execute(sql)

    return items
