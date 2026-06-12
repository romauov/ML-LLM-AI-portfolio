"""
DAG для подготовки данных лидогенератора BERT:
1. Выгрузка userStat
2. Выгрузка текстов объявлений
3. Подсчет эмбеддингов

@author Marat Ibatullin
"""
from datetime import datetime

# pylint: disable=import-error
# pylint: disable=no-name-in-module
from airflow.decorators import dag, task
import pandas as pd

from lib.user_stat_db import user_stat
from lib.tradeboard_db import tradeboard_meatinfo, tradeboard_fishretail
from bert_recommendations.search import get_emeddings

# Названия колонок датасета userStat
TRADEBOARD_COLUMNS = ['id', 'user_id', 'title',
                      'descr', 'city_id', 'region_id', 'human_url_alias']

USERSTAT_COLUMNS = ['userId', 'site', 'userRegion', 'type', 'offerId', 'dealType', 'type1',
                    'type2', 'offerRegion', 'date']

# Индексы сотрудников компании
ADMIN_USERS = [2, 7, 10, 14903, 16005, 34272, 36832, 55508, 55678, 56709, 81860, 94154, 96104,
               99194, 101444, 104849, 135786, 144792, 166055, 171344, 172753, 204902, 207281, 211701, 212080,
               224268, 225329, 233862, 234008, 239509, 253278, 254481, 258944, 259162, 259654, 260854, 260961,
               261124, 261198, 261527, 261870, 262575, 263064, 263659, 263668, 263744, 264599, 266938, 267284]

# pylint: disable=too-many-statements
@dag(schedule="30 0 * * *", start_date=datetime(2024, 1, 28))
def bert_rec_data_preparer():
    """
    Последовательность задач airflow:

    1. Выгрузка userStat без активности админов
    2. Выгрузка текстов объявлений meatinfo
    3. Выгрузка текстов объявлений fishretail
    4. Подсчет эмбеддингов для текстов объявлений и категорий/поисков meatinfo
    5. Подсчет эмбеддингов для текстов объявлений и категорий/поисков fishretail
    """
    @task
    def user_stat_loader():
        data = user_stat()
        df = pd.DataFrame(data, columns=USERSTAT_COLUMNS)
        df = df[df.type != 'search']
        df = df[~df.userId.isin(ADMIN_USERS)]
        path = '/app/apps/file_hosting/bert_recommendations/userStat.parquet'
        print(f"Длина DF userStat: {len(df)}")
        print(f"Длина DF userStat без нанов: {len(df.dropna(subset=['type1', 'type2']))}")
        print(f"Количество записей userStat по сайтам: {df['site'].value_counts()}")
        df.to_parquet(path)

    @task
    def tradeboard_meatinfo_loader():
        data = tradeboard_meatinfo()
        df = pd.DataFrame(data, columns=TRADEBOARD_COLUMNS)
        path = '/app/apps/file_hosting/bert_recommendations/tradeboard.parquet'
        print(f"Длина DF tradeboard meatinfo: {len(df)}")
        print(f"Длина DF tradeboard meatinfo без нанов: {len(df.dropna(subset=['title', 'descr']))}")
        df.to_parquet(path)

    @task
    def tradeboard_fishretail_loader():
        data = tradeboard_fishretail()
        df = pd.DataFrame(data, columns=TRADEBOARD_COLUMNS)
        path = '/app/apps/file_hosting/bert_recommendations/tradeboard_fish.parquet'
        print(f"Длина DF tradeboard fishretail: {len(df)}")
        print(f"Длина DF tradeboard fishretail без нанов: {len(df.dropna(subset=['title', 'descr']))}")
        df.to_parquet(path)

    @task
    def meat_embed():
        user_stat_df = pd.read_parquet(
            "/app/apps/file_hosting/bert_recommendations/userStat.parquet")
        tradeboard = pd.read_parquet(
            "/app/apps/file_hosting/bert_recommendations/tradeboard.parquet")

        user_stat_df = user_stat_df[user_stat_df['site'] == 'meatinfo']

        full_df = user_stat_df.merge(tradeboard, left_on='offerId', right_on='id', how='left')
        full_df = full_df.sort_values(by='date', ascending=False)
        full_df['context'] = full_df['title'] + " " + full_df['descr']
        full_df['search'] = full_df['type1'] + " " + full_df['type2']
        full_df = full_df[['context', 'search',
                           'type', 'user_id', 'userId', 'dealType']]

        advertisment_text = full_df[full_df['dealType'] == 'sale']['context'].dropna().unique()
        search_text = full_df['search'].dropna().unique()

        embeddings = get_emeddings(advertisment_text)
        df_embeddings = pd.DataFrame(embeddings)
        print(f"Длина DF tradeboard meatinfo: {len(df_embeddings)}")
        df_embeddings.to_csv("/app/apps/file_hosting/bert_recommendations/embeddings_meatinfo.csv", index=False)
        embeddings_search = get_emeddings(search_text)
        df_embeddings_search = pd.DataFrame(embeddings_search)
        print(f"Длина DF tradeboard meatinfo: {len(df_embeddings_search)}")
        df_embeddings_search.to_csv(
            "/app/apps/file_hosting/bert_recommendations/embeddings_search_meatinfo.csv", index=False)

    @task
    def fish_embed():
        user_stat_df = pd.read_parquet(
            "/app/apps/file_hosting/bert_recommendations/userStat.parquet")
        tradeboard = pd.read_parquet(
            "/app/apps/file_hosting/bert_recommendations/tradeboard_fish.parquet")

        user_stat_df = user_stat_df[user_stat_df['site'] == 'fishretail']

        full_df = user_stat_df.merge(tradeboard, left_on='offerId', right_on='id', how='left')
        full_df = full_df.sort_values(by='date', ascending=False)
        full_df['context'] = full_df['title'] + " " + full_df['descr']
        full_df['search'] = full_df['type1'] + " " + full_df['type2']
        full_df = full_df[['context', 'search',
                           'type', 'user_id', 'userId', 'dealType']]

        advertisment_text = full_df[full_df['dealType'] == 'sale']['context'].dropna().unique()
        search_text = full_df['search'].dropna().unique()

        embeddings = get_emeddings(advertisment_text)
        df_embeddings = pd.DataFrame(embeddings)
        print(f"Длина DF tradeboard fishretail: {len(df_embeddings)}")
        df_embeddings.to_csv("/app/apps/file_hosting/bert_recommendations/embeddings_fishretail.csv", index=False)
        embeddings_search = get_emeddings(search_text)
        df_embeddings_search = pd.DataFrame(embeddings_search)
        print(f"Длина DF tradeboard fishretail: {len(df_embeddings_search)}")
        df_embeddings_search.to_csv(
            "/app/apps/file_hosting/bert_recommendations/embeddings_search_fishretail.csv", index=False)

    user_stat_task = user_stat_loader()
    tradeboard_meatinfo_task = tradeboard_meatinfo_loader()
    tradeboard_fishretail_task = tradeboard_fishretail_loader()
    meat_embed_task = meat_embed()
    fish_embed_task = fish_embed()

    # pylint: disable=pointless-statement
    user_stat_task >> tradeboard_meatinfo_task >> tradeboard_fishretail_task >> meat_embed_task >> fish_embed_task


bert_rec_data_preparer()
