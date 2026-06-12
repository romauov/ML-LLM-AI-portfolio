"""
DAG для подготовки данных для рекомендации по кластеру:
1. Выгрузка данных из таблицы userStat
2. Выгрузка данных из таблицы tradeboard
3. Создание датасета 'labels_categories.csv' для определения category_name по type1
4. Создание датасета 'clusters.csv', содержащего номера кластеров и эмбеддинги наименований продукции
5. Создание датасета 'userStat_f.csv', userStat за последние полгода с указанием кластера продукции
@author Sergei Romanov
"""

from datetime import datetime
import shutil

import numpy as np
import pandas as pd
import polars as pl
import torch

from sklearn.cluster import KMeans
from transformers import AutoTokenizer, AutoModel
# pylint: disable=import-error
# pylint: disable=(no-name-in-module)
from airflow.decorators import dag, task

from lib.tradeboard_clickhouse import clickhouse_tradeboard

# Названия колонок датасета userStat
TRADEBOARD_COLUMNS = ['itemId', 'site', 'title', 'userId', 'label', 'regionId', 'dealType',
                      'dateCreated', 'dateModified', 'type1', 'type2', 'category_name']

USERSTAT_COLUMNS = ['userId', 'userRegion', 'type', 'offerId', 'dealType', 'type1', 'type2',
                    'offerRegion', 'date']

# Индексы сотрудников компании
ADMIN_USERS = [2, 7, 10, 14903, 16005, 34272, 36832, 55508, 55678, 56709, 81860, 94154, 96104,
               99194, 101444, 104849, 135786, 144792, 166055, 171344, 172753, 204902, 207281, 211701, 212080,
               224268, 225329, 233862, 234008, 239509, 253278, 254481, 258944, 259162, 259654, 260854, 260961,
               261124, 261198, 261527, 261870, 262575, 263064, 263659, 263668, 263744, 264599, 266938, 267284]

# pylint: disable=too-many-statements
@dag(schedule="0 1 * * *", start_date=datetime(2024, 2, 12))
def cluster_recmndr_preparer():
    """Загрузка и преобразование датасетов для использования в сервисе"""
    @task
    def tradeboard_loader():
        tradeboard = pd.DataFrame(clickhouse_tradeboard(), columns=TRADEBOARD_COLUMNS)
        tradeboard.to_parquet(
            '/app/apps/file_hosting/cluster_recmndr/tradeBoard.parquet')

    @task
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals
    def datasets_loader(filter_period=6):
        '''
        Добавление в датасет userStat столбца с кластером продукции и создание датасета с эмбеддингами 
        наименованиий продукциипараметр filter_period задаёт временной интервал с количеством месяцев, 
        за который берётся срез данных
        '''
        # открываем датасет с действиями пользователей
        df = pl.read_csv(
            '/app/apps/file_hosting/knn_recommendations/userStat.csv')
        df = df.select(pl.col(['userId', 'type1', 'type2', 'date']))
        df = df.with_columns(pl.col("type1").str.strip_chars_start())
        df = df.with_columns(pl.col("type1").str.to_lowercase())
        df = df.with_columns(pl.col("type2").str.strip_chars_start())
        df = df.with_columns(pl.col("type2").str.to_lowercase())

        type1_count = df.select(pl.col("type1").value_counts()).unnest('type1')
        partitions_dict = type1_count.partition_by("type1", as_dict=True)
        df = df.with_columns(pl.col("type1").map_elements(lambda x: 'Другое'
                                                          if partitions_dict[x]['count'][0] < 250
                                                          else x))
        df = df.filter(pl.col('type1') != 'Другое')
        type2_count = df.select(pl.col("type2").value_counts()).unnest('type2')
        partitions_dict = type2_count.partition_by("type2", as_dict=True)
        df = df.with_columns(pl.col("type2").map_elements(lambda x: 'Другое'
                                                          if partitions_dict[x]['count'][0] < 250
                                                          else x))
        df = df.filter(pl.col('type2') != 'Другое')

        labels_df = pl.read_parquet(
            '/app/apps/file_hosting/cluster_recmndr/tradeBoard.parquet').drop_nulls(subset=['category_name'])
        labels_df = labels_df.with_columns(
            pl.col("type1").str.strip_chars_start())
        labels_df = labels_df.with_columns(pl.col("type1").str.to_lowercase())
        labels_df = labels_df.unique()
        type1_count = labels_df.select(
            pl.col("type1").value_counts()).unnest('type1')
        partitions_dict = type1_count.partition_by("type1", as_dict=True)

        labels_df = labels_df.with_columns(pl.col("type1").map_elements(lambda x: 'Другое'
                                                                        if partitions_dict[x]['count'][0] < 250
                                                                        else x))
        labels_df = labels_df.filter(pl.col('type1') != 'Другое')
        type1s = labels_df.select(pl.col('type1')).unique()['type1'].to_list()

        labels_df = labels_df.drop_nulls(subset=['category_name'])

        for i, type1s_i in enumerate(type1s):
            categories = labels_df.filter(pl.col('type1') == type1s_i)\
                    .select(pl.col('category_name').value_counts(sort=True))\
                    .unnest('category_name')[0]['category_name']
            if len(categories) > 0:
                major_category = categories[0]
            else:
                major_category = 'Без категории'
            labels_df = labels_df.with_columns((pl.when(pl.col('type1') == type1s_i).then(pl.lit(major_category))
                                                .otherwise(pl.col('category_name'))).alias('category_name'))

        labels_categories = labels_df.select(pl.col(['type1', 'category_name']))\
            .unique(subset=['type1'])
        labels_categories.write_csv(
            '/app/apps/file_hosting/cluster_recmndr/labels_categories.csv')

        df = df.join(labels_categories, how='left', on='type1')
        df = df.with_columns(
            (pl.col('type1') + ' ' + pl.col('type2')).alias('type12'))
        df = df.drop(['type1', 'type2'])

        df = df.with_columns(
            (pl.col('category_name') + ' ' + pl.col('type12')).alias('product'))
        df = df.drop_nulls()
        save_path = '/app/apps/file_hosting/cluster_recmndr/bert'
        cache_path = '/app/apps/file_hosting/cluster_recmndr/cache'
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                save_path, cache_dir=cache_path)
            model = AutoModel.from_pretrained(
                save_path, cache_dir=cache_path)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            print(e)
            pretrained_weights = 'cointegrated/rubert-tiny2'
            tokenizer = AutoTokenizer.from_pretrained(
                pretrained_weights, cache_dir=cache_path)
            tokenizer.save_pretrained(save_path)
            model = AutoModel.from_pretrained(
                pretrained_weights, cache_dir=cache_path)
            model.save_pretrained(save_path)
            shutil.rmtree(cache_path)
        products = df.select(pl.col('product')).unique()['product'].to_list()
        tokenized = tokenizer(products, padding=True, truncation=True)
        tokens = np.array(tokenized['input_ids'])
        attention_mask = np.where(tokens != 0, 1, 0)

        batch_size = 1
        embeddings = []
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = model.to(device)

        for i in (range(len(tokens) // batch_size)):
            try:
                batch = torch.tensor(tokens[batch_size*i:batch_size*(i+1)])
                attention_mask_batch = torch.tensor(
                    attention_mask[batch_size*i:batch_size*(i+1)])
            except IndexError:
                batch = torch.tensor(tokens[batch_size*i:])
                attention_mask_batch = torch.tensor(
                    attention_mask[batch_size*i:])

            with torch.no_grad():
                batch_embeddings = model(
                    batch.to(device), attention_mask=attention_mask_batch.to(device))

            embeddings.append(batch_embeddings[0][:, 0, :].cpu().numpy())

        products_df = pd.DataFrame(
            data=np.concatenate(embeddings), index=products)
        products_df.to_csv('/app/apps/file_hosting/cluster_recmndr/products_df.csv',
                           index=False)

        kmeans = KMeans(n_clusters=121, n_init='auto')
        kmeans.fit(products_df)
        products_df['cluster'] = kmeans.labels_

        products_df['product'] = products_df.index
        products_df = pl.from_pandas(products_df)

        products_df.write_csv('/app/apps/file_hosting/cluster_recmndr/clusters.csv')

        cluster_df = df.join(products_df.select(
            pl.col(['cluster', 'product'])), right_on='product', left_on='product')
        # df_clusters = cluster_df.select(pl.col(['product', 'cluster'])).unique()

        cluster_df = cluster_df.with_columns(pl.col("date").str.to_datetime())

        last_months = pd.Timestamp.today() - pd.offsets.MonthBegin(filter_period)

        filtered_df = cluster_df.filter(pl.col("date") >= last_months, ~(pl.col("userId").is_in(ADMIN_USERS)))
        filtered_df.write_csv('/app/apps/file_hosting/cluster_recmndr/userStat_f.csv')

    tradeboard_task = tradeboard_loader()
    datasets_task = datasets_loader()
    # pylint: disable=pointless-statement
    #datasets_task
    tradeboard_task >> datasets_task
cluster_recmndr_preparer()
