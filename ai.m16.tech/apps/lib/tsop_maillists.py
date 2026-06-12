"""
Выгрузка email пользователей, которые получали рассылку от клиента ЦОПА

@author Dmitry Abramov
"""

from .db import create_connect_db_m16_stage

def tsop_maillisted_users(tsop_id):
    """
    Выгрузка email пользователей, которые получали рассылку от клиента ЦОПА
    в течение последних двух недель

    Возвращает список email пользователей для последующей сортировки 
        в apps/knn_recommendations/recommender
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()
    query = """
            SELECT email.email
            FROM tsop_service.tsop_mailing tm
                    JOIN emailer.email_maillist em ON em.maillist_id = tm.maillist_id
                    JOIN emailer.email email ON email.id = em.email_id
            WHERE tm.tsop_id = %s
                AND tm.created_date > DATE_SUB(NOW(), INTERVAL 14 DAY)
            """
    cursor.execute(query, (tsop_id,))
    data = cursor.fetchall()
    cursor.close()
    return data

def spamers():
    """
    Выгрузка email пользователей, которые отнесены к спамерам и конкурентам M16
    {{MAILLIST_URL}}/mainPage/fullRecipientsList?id=307
    {{MAILLIST_URL}}/mainPage/fullRecipientsList?id=194415
    """
    db = create_connect_db_m16_stage()
    cursor = db.cursor()
    query = """
            SELECT email.email
            FROM emailer.email_maillist em
                JOIN emailer.email email ON email.id = em.email_id
            WHERE em.maillist_id in (307, 194415)
            """
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return data
