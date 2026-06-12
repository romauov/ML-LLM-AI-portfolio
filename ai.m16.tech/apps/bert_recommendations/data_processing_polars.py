"""
Предобработка данных polars для
рекомендаций на основе BERT 

@author Marat Ibatullin
"""
import gc

import polars as pl
from polars import col


# pylint: disable=invalid-name
def init_data_frames_polars(site: str, EMBED_DICT: dict):
    """
       Подготовка необходимого датафрейма и списков: покупателей, текстов объявлений 
       о продаже, текстов поисковых запросов

       arguments:
       site -- сайт по которому строятся рекомендации

       Pipeline состоит из нескольких основных компонентов:
          1. Создание одного df:
             а. Объедние(Merge) userstat и tradeboard по ID объяления
             b. Сортировка по дате
             c. Создание 'context' - объединение название и текста объявления
             d. Создание 'search' - объединение категорий товара
          2. Список покупателей(
             покупатель - человек который ищет товар, смотрит объявления о продаже, создает объявления о покупке и т.д.)
          3. Список уникальных объявлений о продаже
          4. Список уникальных поисковых запросов
    """
    purpose_customer = ["search", 'watch_sale', 'create_buy',
                        'create_up_buy', 'edit_up_buy', 'create_up_buy',
                        'trade_photo_view', 'order_from_trade', 'callButtonTrade']

    user_stat = pl.read_parquet("apps/file_hosting/bert_recommendations/userStat.parquet").filter(
        col('site') == site)
    tradeboard = pl.read_parquet(EMBED_DICT[site][2])
    full_df = user_stat.join(tradeboard, left_on='offerId', right_on='id', how='left')
    del user_stat, tradeboard
    gc.collect()

    full_df = full_df.sort('date', descending=True)
    full_df = full_df.with_columns(pl.concat_str(
        [pl.col('title'), pl.col('descr')], separator=" ").alias("context"))
    full_df = full_df.with_columns(pl.concat_str(
        [pl.col('type1'), pl.col('type2')], separator=" ").alias("search"))
    full_df = full_df.select(
        ['context', 'search', 'type', 'user_id', 'userId', 'dealType'])

    customer_df = full_df.filter(col('type').is_in(
        purpose_customer)).filter(col('userId') != col('user_id'))
    customers_id = customer_df.select('userId').unique(maintain_order=True)
    del customer_df
    gc.collect()

    advertisment_df = full_df.filter(col('dealType') == 'sale')
    advertisment_text = advertisment_df.select(
        'context').drop_nulls().unique(maintain_order=True)
    del advertisment_df
    gc.collect()

    search_text = full_df.select(
        'search').drop_nulls().unique(maintain_order=True)
    return customers_id, advertisment_text, search_text, full_df

def load_emails(site, tsop_id):
    """
    Загрузка и фильтрация списка пользователей
    Фильтрация по спискам отказников и конкурентов, id списков: 307 и 194415
    Фильтрация по пользователям, которые получали рассылку от клиента за последние 2 недели

    Принимает:
        site: str - сайт, с которого берутся емейлы пользователей
        tsop_id: int - id клиента ЦОПА

    Возвращает:
        polars.DataFrame
        ┌────────┬────────────────────────────┐
        │ userId ┆ email                      │
        │ ---    ┆ ---                        │
        │ i64    ┆ str                        │
        ╞════════╪════════════════════════════╡
        │ 1      ┆ 1@mail.ru                  │
        │ 2      ┆ 2k@mail.ru                 │
        └────────┴────────────────────────────┘
    """
    emails = pl.read_csv('apps/file_hosting/knn_recommendations/user_emails.csv')\
        .filter(col('site') == site).select(['userId', 'email'])

    maillisted_users = pl.read_csv('apps/file_hosting/knn_recommendations/maillisted_users.csv')
    spamers = pl.read_csv('apps/file_hosting/knn_recommendations/spamers.csv')

    emails = emails.filter(~pl.col('email').is_in(maillisted_users.filter(pl.col('tsop_id') == tsop_id)['email']))
    emails = emails.filter(~pl.col('email').is_in(spamers['email']))

    del maillisted_users, spamers

    return emails
