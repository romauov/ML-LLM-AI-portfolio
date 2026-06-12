"""
DAG для подготовки данных:
1. Выгрузки userStat
2. Списков спамеров

@author Dmitry Abramov
"""
from datetime import datetime

# pylint: disable=import-error
# pylint: disable=(no-name-in-module)
from airflow.decorators import dag, task
import pandas as pd

from lib.user_stat_db import email_db, user_stat
from lib.tsop_maillists_polars import tsop_maillisted_users, spamers

# Названия колонок датасета userStat
USERSTAT_COLUMNS = ['userId', 'site', 'userRegion', 'type', 'offerId', 'dealType', 'type1',
                    'type2', 'offerRegion', 'date']

# Индексы сотрудников компании
ADMIN_USERS = [2, 7, 10, 14903, 16005, 34272, 36832, 55508, 55678, 56709, 81860, 94154, 96104,
               99194, 101444, 104849, 135786, 144792, 166055, 171344, 172753, 204902, 207281, 211701, 212080,
               224268, 225329, 233862, 234008, 239509, 253278, 254481, 258944, 259162, 259654, 260854, 260961,
               261124, 261198, 261527, 261870, 262575, 263064, 263659, 263668, 263744, 264599, 266938, 267284]


@dag(schedule="0 0 * * *", start_date=datetime(2023, 11, 1))
def tsop_data_preparer():
    """
    Последовательность задач airflow
    """
    @task
    def user_stat_loader():
        data = user_stat()
        df = pd.DataFrame(data, columns=USERSTAT_COLUMNS)
        df = df[df.type != 'search']
        df = df[~df.userId.isin(ADMIN_USERS)]
        df.loc[df.type2 == '', 'type2'] = '1'
        path = '/app/apps/file_hosting/knn_recommendations/userStat.csv'
        df.to_csv(path)
        return path

    @task
    def data_checker(path):
        df = pd.read_csv(path)
        print(f"Длина DF: {len(df)}")
        print(f"Длина DF без нанов: {len(df.dropna(subset=['type1', 'type2']))}")
        print(f"Количество нанов в type1: {len(df[df.type1.isna()])}")
        print(f"Количество нанов в type2: {len(df[df.type2.isna()])}")
        print(f"Количество записей по сайтам: {df['site'].value_counts()}")
        return path

    @task
    def user_ratios(path):
        df = pd.read_csv(path)
        ratios = df.groupby(['userId', 'site']).agg(type1_product=('type1', lambda x: x.value_counts().index),
                                                    type1_ratio=('type1', lambda x: x.value_counts(normalize=True)))
        ratios = ratios.reset_index()
        ratios = ratios.explode(['type1_product', 'type1_ratio'])
        ratios['type1_product'] = ratios['type1_product'].str.lower()
        ratios.to_csv("/app/apps/file_hosting/knn_recommendations/ratios.csv")

    @task
    def emails_loader():
        df = email_db()
        df = pd.DataFrame(df, columns=['userId', 'email', 'site'])
        df = df.dropna().drop_duplicates(subset=['email','userId'])
        df.to_csv("/app/apps/file_hosting/knn_recommendations/user_emails.csv")

    @task
    def maillisted_users():
        data = tsop_maillisted_users()
        df = pd.DataFrame(data, columns=['tsop_id', 'email'])
        df.to_csv("/app/apps/file_hosting/knn_recommendations/maillisted_users.csv")

    @task
    def tsop_spamers():
        data = spamers()
        df = pd.DataFrame(data, columns=['email'])
        df.to_csv("/app/apps/file_hosting/knn_recommendations/spamers.csv")

    path = user_stat_loader()
    data_checker_task = data_checker(path)
    user_ratios_task = user_ratios(data_checker_task)
    emails_task = emails_loader()
    maillisted_users_task = maillisted_users()
    tsop_spamers_task = tsop_spamers()

    # pylint: disable=pointless-statement
    path >> data_checker_task >> user_ratios_task >> emails_task >> maillisted_users_task >> tsop_spamers_task


tsop_data_preparer()
