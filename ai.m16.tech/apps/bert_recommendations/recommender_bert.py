"""
Построение рекомендаций
при помощи векторного поиска и агрегирования данных

@author Marat Ibatullin
"""
import logging
import gc

import numpy as np
import polars as pl
from polars import col
import pandas as pd

from .search import index_init, search_for, set_found
from .data_processing import init_data_frames
from .data_processing_polars import init_data_frames_polars, load_emails
from . import EMBED_DICT

def logger_innit():
    """
    Инициализация логгера
    """
    logger_system = logging.getLogger("bert_rec_system_logger")
    formatter = logging.Formatter('[%(levelname)-10s] %(asctime)-25s - %(message)s')
    file_handler_system  = logging.FileHandler(filename='log/bert_rec_system_log.log',
                                               mode='a',
                                               encoding='utf-8')
    file_handler_system.setFormatter(formatter)
    logger_system.addHandler(file_handler_system)
    logger_system.setLevel(logging.INFO)
    return logger_system


def recommendation(context, search, number_of_users, site, tsop_id):
    """
    Построение рекомендаций (pandas)

    arguments:
        context -- Текст продвигаемого объявления
        search -- Тип товара
        number_of_users -- колличество релевантных пользователей для рассылки
        site -- сайт на котором происходит поиск

    Pipeline состоит из нескольких основных компонентов:
            1. Считываение эмбеддингов из csv
            2. Обучение вектороного пространства для поиска сходих векторов
            3. Наполнение списка похожих объявлений и поисков
            4. Агрегация данных по похожим объявлениям и времени
    """
    logger_system = logging.getLogger("bert_rec_system_logger")

    if len(logger_system.handlers) == 0:
        logger_system = logger_innit()

    customers_id, advertisment_text, search_text, full_df = init_data_frames(
        site, EMBED_DICT)

    embeddings = pl.read_csv(EMBED_DICT[site][0])
    embeddings = np.array(embeddings).astype('float32')
    embeddings_search = pl.read_csv(EMBED_DICT[site][1])
    embeddings_search = np.array(embeddings_search).astype('float32')

    input_log = f"Полученный запрос: Текст объявления: {context}, Поисковый запрос: {search}"
    logger_system.info(input_log)

    faiss_index_context,  faiss_index_search = index_init(
        embeddings, embeddings_search)
    logger_system.info("Векторный движок обучен.")
    del  embeddings, embeddings_search
    gc.collect()

    reccomend = pd.Series(dtype='object')
    neighbors = 0

    while len(reccomend) < number_of_users:
        if neighbors < 40:
            neighbors += 10
            staff_to_found = []
            staff_to_found += set_found(search_for(faiss_index_context,
                                        context, neighbors), advertisment_text)
            staff_to_found += set_found(search_for(faiss_index_search,
                                        search, neighbors), search_text)
            logger_system.info("Рекомендации составлены. Количество соседей %d.", neighbors)

            reccomend = full_df[(full_df['userId'].isin(customers_id)) &
                                 ((full_df['context'].isin(staff_to_found)) |
                                 (full_df['search'].isin(staff_to_found))) &
                                 (full_df['userId'] != full_df['user_id'])]
        else:
            logger_system.warning("Рекомендации составлены на основе последних действий.")
            reccomend = full_df[(full_df['userId'].isin(customers_id)) &
                                 (full_df['userId'] != full_df['user_id'])]

    if len(reccomend) != 0:
        for i in range(neighbors):
            logger_system.info("Текст похожего объявления: %s.", staff_to_found[i])
        for i in range(neighbors):
            logger_system.info("Текст похожего поискового запроса: %s.", staff_to_found[neighbors + i])
    del customers_id, advertisment_text, search_text, full_df
    gc.collect()
    faiss_index_context.reset()
    faiss_index_search.reset()

    emails = load_emails(site, tsop_id)

    reccomend = reccomend[['userId']].drop_duplicates()

    reccomend = reccomend.merge(emails.to_pandas(), on='userId', how='inner')[:number_of_users]
    reccomend = {'Emails': reccomend['email'].to_list(),
                 'Id': reccomend['userId'].to_list()}

    return reccomend


def recommendation_polars(context, search, number_of_users, site, tsop_id):
    """
    Построение рекомендаций (pandas)

    arguments:
        context -- Текст продвигаемого объявления
        search -- Тип товара
        number_of_users -- колличество релевантных пользователей для рассылки
        site -- сайт на котором происходит поиск

    Pipeline состоит из нескольких основных компонентов:
            1. Считываение эмбеддингов из csv
            2. Обучение вектороного пространства для поиска сходих векторов
            3. Наполнение списка похожих объявлений и поисков
            4. Агрегация данных по похожим объявлениям и времени
    """
    logger_system = logging.getLogger("bert_rec_system_logger")
    if len(logger_system.handlers) == 0:
        logger_system = logger_innit()

    customers_id, advertisment_text, search_text, full_df = init_data_frames_polars(
        site, EMBED_DICT)
    embeddings = pl.read_csv(EMBED_DICT[site][0])
    embeddings = np.array(embeddings).astype('float32')
    embeddings_search = pl.read_csv(EMBED_DICT[site][1])
    embeddings_search = np.array(embeddings_search).astype('float32')

    faiss_index_context,  faiss_index_search = index_init(
        embeddings, embeddings_search)
    del  embeddings, embeddings_search
    gc.collect()
    logger_system.info("Векторный движок обучен.")

    reccomend = pl.Series()
    neighbors = 0

    emails = load_emails(site, tsop_id)

    while len(reccomend) < number_of_users:
        if neighbors < 40:
            neighbors += 10
            staff_to_found = []
            staff_to_found += set_found(search_for(faiss_index_context,
                                        context, neighbors), advertisment_text['context'].to_list())
            staff_to_found += set_found(search_for(faiss_index_search,
                                        search, neighbors), search_text['search'].to_list())
            logger_system.info("Рекомендации составлены. Количество соседей %d.", neighbors)

            reccomend = full_df.filter((col('userId').is_in(customers_id['userId'].to_list())) &
                                        ((full_df['context'].is_in(staff_to_found)) |
                                        (full_df['search'].is_in(staff_to_found))) &
                                        ((col('userId') != col('user_id')) |
                                         col('user_id').is_null())).select('userId').unique()
        else:
            logger_system.warning("Рекомендации составлены на основе последних действий.")
            reccomend = full_df.filter((col('userId').is_in(customers_id['userId'].to_list())) &
                                        ((col('userId') != col('user_id')) |
                                        col('user_id').is_null()))['userId'].select('userId').unique()

        reccomend = reccomend.join(emails, on='userId', how='inner')

    if len(reccomend) != 0:
        for i in range(neighbors):
            logger_system.info("Текст похожего объявления: %s.", staff_to_found[i])
        for i in range(neighbors):
            logger_system.info("Текст похожего поискового запроса: %s.", staff_to_found[neighbors + i])

    del customers_id, advertisment_text, search_text, full_df

    gc.collect()
    faiss_index_context.reset()
    faiss_index_search.reset()

    reccomend = reccomend[:number_of_users]
    reccomend = {'Emails': reccomend['email'].to_list(),
                 'Id': reccomend['userId'].to_list()}

    return reccomend
