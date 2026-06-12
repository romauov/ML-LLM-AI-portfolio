"""
Предобработка данных pandas для
рекомендаций на основе BERT 

@author Marat Ibatullin
"""
import gc

import pandas as pd


# pylint: disable=invalid-name
def init_data_frames(site: str, EMBED_DICT: dict):
    """
        Подготовка необходимого датафрейма и списков: покупателей, текстов объявлений о продаже, 
        текстов поисковых запросов

        arguments:
        site -- сайт по которому строятся рекомендации

        Pipeline состоит из нескольких основных компонентов:
            1. Создание одного df:
                а. Объедние(Merge) userstat и tradeboard по ID объяления
                b. Сортировка по дате
                c. Создание 'context' - объединение название и текста объявления
                d. Создание 'search' - объединение категорий товара
            2. Список покупателей(
                покупатель - человек который ищет товар, смотрит объявления о продаже, 
                создает объявления о покупке и т.д.)
            3. Список уникальных объявлений о продаже
            4. Список уникальных поисковых запросов
    """

    purpose_customer = ["search", 'watch_sale', 'create_buy',
                        'create_up_buy', 'edit_up_buy', 'create_up_buy',
                        'trade_photo_view', 'order_from_trade', 'callButtonTrade']

    user_stat = pd.read_parquet(
        "apps/file_hosting/bert_recommendations/userStat.parquet")
    tradeboard = pd.read_parquet(EMBED_DICT[site][2])

    user_stat = user_stat[user_stat['site'] == site]
    full_df = user_stat.merge(tradeboard, left_on='offerId', right_on='id', how = 'left')
    del user_stat, tradeboard
    gc.collect()

    full_df = full_df.sort_values(by='date', ascending=False)
    full_df['context'] = full_df['title'] + " " + full_df['descr']
    full_df['search'] = full_df['type1'] + " " + full_df['type2']

    customer_df = full_df[full_df['type'].isin(purpose_customer)]
    customer_df = customer_df[~(
        customer_df['userId'] == customer_df['user_id'])]
    customers_id = customer_df['userId'].unique()
    del customer_df
    gc.collect()

    advertisment_text = full_df[full_df['dealType'] == 'sale']['context'].dropna().unique()
    search_text = full_df['search'].dropna().unique()

    full_df = full_df[['context', 'search', 'type', 'user_id', 'userId', 'dealType']]

    return customers_id, advertisment_text, search_text, full_df
