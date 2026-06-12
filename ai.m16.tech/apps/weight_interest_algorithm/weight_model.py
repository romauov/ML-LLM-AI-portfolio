"""
Формирование списка пользователей для рассылки

Машинное обучение не используется, список формируется на основе данных о пользовательской активности

@author Sergey Vakhrameev
"""

from collections import defaultdict

import pandas as pd
import numpy as np

from dateutil.relativedelta import relativedelta

from lib.logs import message
from lib.user_stat_db import user_stat
from .config import WEIGHTS, ADMIN_USERS
from . import db

# pylint: disable=too-many-arguments


def def_value():
    """
    Возврат 0 как дефолтное значение для defaultdict
    """
    return 0

def get_user_stat(number_of_days, site) -> pd.DataFrame:
    """
    Загрузка таблицы axe.userStat из Clickhouse
    """
    data = user_stat(number_of_days, site)
    df = pd.DataFrame(data, columns=['userId', 'userRegion', 'type', 'offerId', 'dealType',
                                     'type1', 'type2', 'offerRegion', 'date'])
    df['date'] = pd.to_datetime(df['date'])
    df['type1'] = df['type1'].str.capitalize()
    df['type2'] = df['type2'].str.capitalize()
    df['type2'] = df['type2'].fillna('Unknown_type')

    return df


def get_mailing_stats(number_of_days, site) -> pd.DataFrame:
    """
    Загрузка таблицы со статистикой действий пользователя из Clickhouse
    """
    data = db.user_mailing_activities(number_of_days, site)
    mailing_views = pd.DataFrame(data, columns=['email', 'userId', 'axeId', 'sent', 'open', 'date_sent', 'date_open'])
    mailing_views.date_sent = pd.to_datetime(mailing_views.date_sent)
    mailing_views.date_open = pd.to_datetime(mailing_views.date_open)

    return mailing_views


def get_unsubscribed_users(axe_id) -> pd.DataFrame:
    """
    Загрузка отписавшихся пользователей из таблицы emailer.email_maillist MySQL
    """
    data = db.unsubscribed_from_mailing_users(axe_id)
    unsubscribed_users = pd.DataFrame(data, columns=['email', '1', '2'])['email']

    return unsubscribed_users


def get_non_opening_users() -> pd.DataFrame:
    """
    Загрузка неоткрывающих рассылку пользователей из таблицы emailer.email_maillist MySQL
    """
    data = db.non_opening_users()
    return list(data)


def remove_employees(df: pd.DataFrame) -> pd.DataFrame:
    """
    Удаление индексов сотрудников
    """
    return df.drop(df[df['userId'].isin(ADMIN_USERS)].index)


def cut_events(df: pd.DataFrame, number_of_days: int) -> pd.DataFrame:
    """
    Оставляем только тех пользователей, которые проявляли активность за последние number_of_days дней
    """
    date = pd.to_datetime('today').normalize() - relativedelta(days=number_of_days)

    return df[df['date'] >= date]


def process_with_subcat_df(df: pd.DataFrame, weight_dict: defaultdict, categories: dict) -> pd.DataFrame:
    """
    Оставляем только строки с нужными значениями type, type1, type2
    """
    temp_df = df[df['type'].isin(weight_dict.keys())]
    valid_df = pd.DataFrame(columns=df.columns)
    for category, subcategories in categories.items():
        needed_cat = temp_df[temp_df['type1'] == category]
        if len(subcategories) >= 1:
            needed_cat = needed_cat[needed_cat['type2'].isin(subcategories)]
        valid_df = pd.concat([valid_df, needed_cat], ignore_index=True)

    # temp_df = temp_df[temp_df['type1'].isin(categories.keys())]
    # temp_df = temp_df[temp_df['type2'].isin(sum(categories.values(), []))]

    # кодируем type
    temp_df = valid_df.replace({'type': weight_dict})

    # преобразовываем исходную таблицу
    temp_df = temp_df.astype({'userId': 'str', 'type': 'str'})
    temp_df = temp_df.groupby(['type1', 'type2', 'userId'])['type'] \
        .agg(lambda x: sum((int(i) for i in x))) # тут пропадают значения поисков
    temp_df = temp_df.unstack(['type1', 'type2'])

    return temp_df.fillna(0)


def get_users_by_category(df: pd.DataFrame, min_user_activity_level: int) -> pd.DataFrame:
    """
    Убираем случайно нажавших на объявление, либо неактивных пользователей 
    """
    users = df.sum(axis='columns').sort_values(ascending=False)
    users = users.loc[users.values > min_user_activity_level]

    # print('С данной категорией взаимодействовало {} из {} пользователей'.format(len(users), num_of_users))
    return users


def get_valid_users_ids(axe_id,
                        mailing_views,
                        potential_users,
                        last_mail_opening_date,
                        sent_to_opened_relation) -> list:
    """
    Берем подобранных алгоритмом пользователей
    Убираем пользователей, у которых уже была рассылка сегодня (date_sent == today)
    и тех, у кого была рассылка у данного акса в последние 3 недели
    и тех, кто мало просматривает рассылки
    """
    potential_users.index = potential_users.index.astype(int)
    # оставляем пользователей, подобранных алгоритмом
    mailing_views = mailing_views[mailing_views.userId.isin(i for i in potential_users.index)]
    # убираем тех, у кого была рассылка у данного акса в последние 3 недели.
    users_to_drop = mailing_views[mailing_views['axeId'] == axe_id]
    users_to_drop = users_to_drop[users_to_drop['date_sent'] > \
                                  (pd.to_datetime('today').normalize() - relativedelta(days = 22))]['userId'].values
    mailing_views = mailing_views.drop(mailing_views[mailing_views['userId'] \
                                                     .isin(users_to_drop)].index)
    # print_below = mailing_views.groupby('userId').last().shape[0]
    # message(f'После фильтрации тех, у кого была рассылка в последние 3 недели: {print_below}')
    # убираем тех, у кого была рассылка сегодня
    mailing_views = mailing_views.groupby('userId').agg({
        'email': ['last'], 
        'sent': ['sum'], 
        'open': ['sum'], 
        'date_sent': ['max'],
        'date_open': ['max']
        }).droplevel(1, axis = 1) # сводная статистика открытий по каждому пользователю без привязки к axe'ам

    mailing_views = mailing_views[mailing_views['date_sent'] < pd.to_datetime('today').normalize()]
    # message(f'После фильтрации тех, у кого была рассылка сегодня: {mailing_views.shape[0]}')
    # убираем тех, кто плохо смотрит рассылки
    active_users = mailing_views[mailing_views['date_open'] >= pd.to_datetime(last_mail_opening_date)] \
        [mailing_views['date_open'] >= mailing_views['date_sent']] \
        [(mailing_views['open'] / mailing_views['sent']) >= sent_to_opened_relation] \
            .groupby('userId').last()['email'] #.index

    # но небольшую часть оставляем
    users_to_add = np.random.choice(mailing_views.index[~(mailing_views.index.isin(active_users))] \
                                    .values, size = np.int_(len(active_users) * 0.1))
    users_to_add = mailing_views[mailing_views.index.isin(users_to_add)]['email']
    all_users = pd.concat([active_users, users_to_add]).to_frame()

    return len(users_to_add), \
        pd.merge(all_users, potential_users.to_frame(name='score'), left_index=True, right_index=True)


def get_users(categories,
              number_of_users,
              number_of_days,
              min_user_activity_level,
              last_mail_opening_date = None,
              sent_to_opened_relation = None,
              axe_id = None,
              site = 'meatinfo'):
    """
    Получение параметров для фильтрации пользователей,
    возвращение списка пользователей
    """
    categories = {key.capitalize(): [value.capitalize() for value in values] for key, values in categories.items()}

    weight_dict = defaultdict(def_value)
    for key, _ in WEIGHTS.items():
        weight_dict[key] = WEIGHTS[key]

    user_df = get_user_stat(number_of_days, site)

    mailing_views_axe = get_mailing_stats(number_of_days, site)
    inactive_users_list = get_non_opening_users()
    if axe_id:
        unsubscribed_users = get_unsubscribed_users(axe_id)
    log_1 = user_df.groupby('userId').last().shape[0]

    user_df_processing = remove_employees(user_df)
    # message(f'После фильтрации сотрудников: {user_df_processing.userId.nunique()}')
    user_item_matrix = process_with_subcat_df(user_df_processing, weight_dict, categories)
    log_2 = user_item_matrix.shape[0]
    # message(f'После фильтрации по указанным категориям: {log_2}')
    user_item_matrix_normalized = (user_item_matrix-user_item_matrix.min())/(user_item_matrix.max() \
                                                                             -user_item_matrix.min())
    users = get_users_by_category(user_item_matrix_normalized, min_user_activity_level)
    log_3 = users.shape[0]
    # message(f'После фильтрации по пороговому значению активности: {log_3}')
    if last_mail_opening_date and sent_to_opened_relation and axe_id:
        random_users_len, users = get_valid_users_ids(axe_id,
                                                    mailing_views_axe,
                                                    users,
                                                    last_mail_opening_date,
                                                    sent_to_opened_relation)
        log_4, log_5 = len(users), random_users_len
        # message(f'После фильтрации по дате последнего открытия рассылки и доле открытых рассылок: \
        # {log_4}, из них {random_users_len} - случайные неактивные пользователи')

        users = users[~users.isin(unsubscribed_users)]
        # message(f'После фильтрации отписавшихся: {len(users)}')
        users = users[~users.index.isin(inactive_users_list)]
        # message(f'После фильтрации emails.csv: {len(users)}')
        users = users.sort_values(by='score', ascending=False)
    else:
        log_4, log_5 = '-', '-'
        users.index = users.index.astype(int)
        users = pd.merge(mailing_views_axe.groupby(['userId']).last()[['email']],
                         users.to_frame(name='score'), left_index=True, right_index=True)

    # return [{'email': row[0], 'value': round(row[1], 3)} for row in users.values.tolist()]
    ret_list = list(users['email'].values)[:number_of_users]

    logs = f'''
    После фильтрации по периоду активности: {log_1},\n
    После фильтрации по указанным категориям: {log_2},\n
    После фильтрации по пороговому значению активности: {log_3}, \n
    После фильтрации по дате последнего открытия рассылки и доле открытых рассылок: \
    {log_4}, из них {log_5} - случайные неактивные пользователи,\n
    После фильтрации отписавшихся - итоговое количество email'ов: {len(ret_list)}
            '''
    message(logs)

    return ret_list, logs
