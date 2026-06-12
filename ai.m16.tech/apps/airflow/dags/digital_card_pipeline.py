"""
DAG для подготовки данных для цифровых карточек:
1. Выгрузка данных ФИО, id, должность, дата создания аккаунта
2. Выгрузка данных из таблицы userStat
3. Выгрузка данных из таблицы tradeboard
4. Выгрузка данных из таблицы user_profile
5. Выгрузка данных из таблицы fishretail
6. Выгрузка данных из таблицы meat_info
7. Выгрузка данных с информацией о копаниях
8. Получение данных для каждого пользователя о количестве открытых и полученных писем с рассылкой
9. Получение данных для каждого пользователя о количестве просматриваемых объявлениях
10. Получение данных для каждого пользователя о количестве выставленных объявлениях
11. Получение данных для каждого пользователя о его последней активности
12. Получение данных для каждого пользователя type1 и type2 по объявлениям


@author Yaroslav Koltashev
"""
from datetime import datetime, timedelta

# pylint: disable=import-error
# pylint: disable=no-name-in-module
from airflow.decorators import dag, task
import pandas as pd

from lib.digital_card import (
    user_stat,
    user_stat_buy_sale,
    create_name_id_data_position,
    create_company,
    create_count_send_open,
    create_type1_type2,
    create_last_actions,
    watch_buy_sale,
    create_buy_sale,
    create_fishretail,
    create_meat_info,
    tradeboard,
    user_profile,
    top_5,
    create_action,
    crate_advertisements
)

columns_block_1 = ['userId', 'position', 'firstname', 'lastname', 'dateCreated', 'regionId']
columns_block_2 = ['userId', 'create_sale', 'create_buy', 'create_sale_count', 'create_buy_count']
columns_block_3 = ['userId', 'watch_sale', 'watch_buy', 'watch_sale_count', 'watch_buy_count']
columns_block_4 = ['userId', 'title', 'type1', 'type2']
columns_block_5 = ['userId', 'last_action_date']
columns_user_stat = ['userId', 'itemId', 'site', 'type', 'dateEvent']
columns_user_profile = ['userId', 'login', 'site']
columns_tradeboard = ['itemId', 'userId', 'title', 'label', 'category_name', 'site', 'dateCreated']
columns_count_send_open = ['user_id', 'count_send_mail', 'count_open_email', 'email']
columns_company = ['company_id', 'name_ru', 'description_ru', 'name_ru.1', 'address_ru', 'company_inn', 'region_id']
columns_meatinfo = ['user_id', 'meatinfo_company_id']
columns_fishretail = ['user_id', 'fishretail_company_id']
columns_userstat_buy_sale = ['userId', 'itemId', 'site', 'type', 'dateEvent']


# pylint: disable=too-many-statements
@dag(schedule="15 0 * * 1", start_date=datetime(2023, 11, 27))
def create_digital_card():
    """
    Получение карточки пользователя
    """
    @task
    def create_csv_data():
        # Получаем данные для первого блока
        # ('userId', 'position', 'firstname', 'lastname', 'dateCreated', 'regionId')
        data_block_1 = create_name_id_data_position()
        data_block_1 = pd.DataFrame(data_block_1, columns=columns_block_1)
        data_block_1 = data_block_1.fillna('не определено')
        print(f'Блок 1: {data_block_1.shape}')

        # Получаем данные для второго блока
        # ('userId', 'create_sale', 'create_buy', 'create_sale_count', 'create_buy_count')
        data_block_2 = create_buy_sale()
        data_block_2 = pd.DataFrame(data_block_2, columns=columns_block_2)
        data_block_2 = data_block_2.fillna(0)
        print(f'Блок 2: {data_block_2.shape}')

        # Получаем данные для третьего блока
        # ('userId', 'watch_sale', 'watch_buy', 'watch_sale_count', 'watch_buy_count')
        data_block_3 = watch_buy_sale()
        data_block_3 = pd.DataFrame(data_block_3, columns=columns_block_3)
        data_block_3 = data_block_3.fillna(0)
        print(f'Блок 3: {data_block_3.shape}')

        # Получаем данные для четвёртого блока
        # ('userId', 'title', 'type1', 'type2')
        data_block_4 = create_type1_type2()
        data_block_4 = pd.DataFrame(data_block_4, columns=columns_block_4)
        data_block_4 = data_block_4.fillna('не определено')
        print(f'Блок 4: {data_block_4.shape}')

        top_5_type1 = top_5(data_block_4, 'type1')
        top_5_type2 = top_5(data_block_4, 'type2')

        # Получаем данные для пятого блока
        # ('userId', 'last_action_date')
        data_block_5 = create_last_actions()
        data_block_5 = pd.DataFrame(data_block_5, columns=columns_block_5)
        data_block_5['last_action_date'] = pd.to_datetime(
            data_block_5['last_action_date'])
        week = datetime.now() - timedelta(days=31*2)  # За 2 месяца
        data_block_5['is_active'] = data_block_5['last_action_date'].apply(
            lambda x: 'активный' if x > week else 'не активный')
        print(f'Блок 5: {data_block_5.shape}')

        # Мерджим колонки
        card = data_block_1.merge(data_block_2, on='userId')
        card = card.merge(data_block_3, on='userId')
        card = card.merge(top_5_type1, on='userId')
        card = card.merge(top_5_type2, on='userId')
        card = card.merge(data_block_5, on='userId')
        print(f'Кол-во элементов после первого мерджа: {card.shape}')
        # Получение последней активности пользователей, объявлений и информации о компании
        user_stat_df = user_stat()
        user_stat_df = pd.DataFrame(user_stat_df, columns=columns_user_stat)
        user_stat_df = user_stat_df[user_stat_df['userId'].isin(card['userId'].unique())]
        user_stat_df['dateEvent'] = pd.to_datetime(user_stat_df['dateEvent'])

        user_profile_df = user_profile()
        user_profile_df = pd.DataFrame(user_profile_df, columns=columns_user_profile)

        trade_df = tradeboard()
        trade_df = pd.DataFrame(trade_df, columns=columns_tradeboard)

        # Мерджим таблицы userStat, userProfile, tradeboard
        mg_us_up_t = user_stat_df.merge(user_profile_df, on='userId')
        mg_us_up_t = mg_us_up_t.merge(trade_df, on='itemId')
        mg_us_up_t = mg_us_up_t.fillna('не определено')
        mg_us_up_t = mg_us_up_t.rename(columns={"userId_x": "userId"})

        # получаем таблицу с email пользователей
        email_table = mg_us_up_t[['userId', 'login']].groupby(
            'userId', as_index=False).last()

        # Мерджим с основной таблицей
        card = card.merge(email_table, on='userId')
        card = card.rename(columns={'login': 'email'})
        print(f'Кол-во элементов после второго мерджа: {card.shape}')

        # Получаем последние действия для каждого пользователя
        card['last_action'] = card['userId'].apply(
            lambda x: create_action(x, mg_us_up_t))

        # Создаём таблицу с количеством отправленных и полученных писем для каждого пользователя
        count_send_open = create_count_send_open()
        count_send_open = pd.DataFrame(
            count_send_open, columns=columns_count_send_open)

        # Мерджим с основной таблицей
        card = card.merge(count_send_open.drop(
            columns=['user_id']), on='email', how='left')
        print(f'Кол-во элементов после третьего мерджа: {card.shape}')

        # Получаем информацию о компаниях, в которых пользователь работает
        company = create_company()
        company = pd.DataFrame(company, columns=columns_company)
        company = company.groupby('company_id', as_index=False).last()

        # Таблица meatinfo
        meatinfo = create_meat_info()
        meatinfo = pd.DataFrame(meatinfo, columns=columns_meatinfo)
        meatinfo_company = meatinfo.merge(
            company,
            left_on='meatinfo_company_id',
            right_on='company_id'
        )
        meatinfo_company = meatinfo_company.drop(
            columns=['meatinfo_company_id', 'company_id'])

        # Таблица fishretail
        fishretail = create_fishretail()
        fishretail = pd.DataFrame(fishretail, columns=columns_fishretail)
        fishretail_company = fishretail.merge(
            company,
            left_on='fishretail_company_id',
            right_on='company_id',
        )
        fishretail_company = fishretail_company.drop(
            columns=['fishretail_company_id', 'company_id'])

        # Мерджим таблицы с компаниями
        card = card.merge(
            meatinfo_company,
            left_on='userId',
            right_on='user_id',
            how='left'
        )
        card = card.merge(
            fishretail_company,
            left_on='userId',
            right_on='user_id',
            how='left',
            suffixes=['_meatinfo', '_fishretail']
        )
        print(f'Кол-во элементов после четвёртого мерджа: {card.shape}')

        # Таблица с объявлениями для каждого пользователя
        user_stat_bs = user_stat_buy_sale()
        user_stat_bs = pd.DataFrame(
            user_stat_bs, columns=columns_userstat_buy_sale)
        user_stat_bs['dateEvent'] = pd.to_datetime(user_stat_bs['dateEvent'])
        user_stat_bs['dateEvent'] = user_stat_bs['dateEvent'].dt.strftime(
            '%Y-%m-%d')

        us_for_user = user_stat_bs[['itemId', 'type']]
        table = us_for_user.merge(
            trade_df[[
                'userId',
                'itemId',
                'title',
                'label',
                'category_name',
                'dateCreated'
            ]],
            on='itemId'
        )

        card['advertisements'] = card['userId'].apply(
            lambda x: crate_advertisements(x, table))
        print(f'Вся таблица: {card.info()}')

        # Сохраняем csv
        card.to_csv('/app/apps/file_hosting/digital_user_cards/data_card.csv', index=False)

    path = create_csv_data()
    # pylint: disable=pointless-statement
    path

create_digital_card()
