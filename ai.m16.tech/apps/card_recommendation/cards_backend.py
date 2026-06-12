"""
Рекомендации на основе суммаризованной карточки пользователя

@author Marat Ibatullin
"""
import logging

import faiss
import numpy as np
import pandas as pd

from bert_recommendations.search import model_init, embed_bert_cls
from bert_recommendations.data_processing_polars import load_emails

from . import EMBED_DICT

def logger_innit():
    """
    Инициализация логгера
    """
    logger_system = logging.getLogger("card_rec_system_logger")
    formatter = logging.Formatter('[%(levelname)-10s] %(asctime)-25s - %(message)s')
    file_handler_system  = logging.FileHandler(filename='log/card_rec_system_log.log',
                                               mode='a',
                                               encoding='utf-8')
    file_handler_system.setFormatter(formatter)
    logger_system.addHandler(file_handler_system)
    logger_system.setLevel(logging.INFO)
    return logger_system

def index_init(query: str, site: str, num_results: int = 100, tsop_id: int = 1):
    """
    Построение рекомендаций

    arguments:
        query -- Портер пользователя, на основе которого делается рекомендация
        site -- сайт на котором происходит поиск
        num_results -- колличество релевантных пользователей для рассылки
        tsop_id -- id пользователя ЦОП

    Pipeline состоит из нескольких основных компонентов:
            1. Векторизация суммаризированной карточки
            2. Получение пользователей и эмбеддингов полученных из их карточек
            3. Обучение faiss-индекса считанными эмбеддингами
            4. Агрегация данных
    
    Возвращает словарь {'Emails':[], 'Id':[]}
    """
    logger_system = logging.getLogger("card_rec_system_logger")

    if len(logger_system.handlers) == 0:
        logger_system = logger_innit()

    model, tokenizer = model_init("apps/card_recommendation/model")
    query_embedding = embed_bert_cls(query, model, tokenizer)
    dimension = np.shape(query_embedding)[0]

    input_log = f"Строчка для получения эмбедднига: {query}"
    logger_system.info(input_log)

    path_cards = EMBED_DICT[site][0]
    path_embed = EMBED_DICT[site][1]

    ids = pd.read_csv(path_cards,usecols=['id']).values.flatten()
    embed = pd.read_csv(path_embed)

    float_list = np.array([float(num_str) for num_str in embed.columns])
    embeddings = np.vstack([float_list, embed.values])

    input_log = f"Длина ids: {np.shape(ids)[0]}"
    logger_system.info(input_log)
    input_log = f"Длина embeddings: {np.shape(embeddings)[0]}"
    logger_system.info(input_log)

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)# pylint: disable=no-value-for-parameter
    query_vector = np.array([query_embedding]).astype('float32')
    _, indexes = index.search(query_vector, 1500) # pylint: disable=unused-variable, no-value-for-parameter

    result = ids[indexes].flatten()
    emails = load_emails(site, tsop_id)

    df_id = pd.DataFrame(result, columns=['userId'])

    df_id = df_id.merge(emails.to_pandas(), on='userId', how='inner')[:num_results]
    df_id = {'Emails': df_id['email'].to_list(),
                 'Id': df_id['userId'].to_list()}

    return df_id
