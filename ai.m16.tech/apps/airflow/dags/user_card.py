"""
DAG для подготовки данных для формирования карточки пользователя:
1. Выгрузка данных из таблицы catalogue_company
2. Выгрузка данных из таблицы fishretail_userprofile
3. Выгрузка данных из таблицы meatinfo_userprofile
4. Выгрузка данных из таблицы geobaza_region
@author Sergei Romanov
"""

from datetime import datetime
import pandas as pd

# pylint: disable=import-error
# pylint: disable=(no-name-in-module)
from airflow.decorators import dag, task

from lib.user_card import create_add_date, create_company, create_fishretail,\
    create_last_date, create_meatinfo, create_regions, create_user_stat

# Названия колонок датасета userStat
ADD_DATE_COLUMNS = ['userId', 'site', 'dateAdd']

COMPANY_COLUMNS = ['id', 'name_ru', 'url', 'company_inn', 'director_ru', 'image_id', 'description_ru']

LAST_DATE_COLUMNS = ['userId', 'site', 'last_date']

MEAT_FISH_COLUMNS = ['user_id', 'firstname', 'lastname', 'company_id', 'position', 'activity',
                     'phone', 'phone_privacy', 'mobilephone', 'mobilephone_privacy', 
                     'site', 'icq', 'gtalk', 'skype', 'viber', 'whats_app', 'telegram', 'date_modify']

REGION_COLUMNS = ['id', 'name']

USERSTAT_COLUMNS = ['userId', 'site', 'userRegion', 'type', 'offerId', 'dealType', 'type1',
                    'type2', 'offerRegion', 'date']


@dag(schedule="0 1 * * *", start_date=datetime(2024, 3, 29))
def user_card_preparer():
    """Загрузка датасетов для использования в сервисе
    """
    @task
    def add_date_loader():
        """Выгрузка данных с датой регистрации пользователя
        """
        add_df = pd.DataFrame(create_add_date(), columns=ADD_DATE_COLUMNS)
        add_df.to_csv(
            '/app/apps/file_hosting/user_card/date_add.csv')
    @task
    def company_loader():
        """Выгрузка данных из таблицы catalogue_company
        """
        company = pd.DataFrame(create_company(), columns=COMPANY_COLUMNS)
        company.to_csv(
            '/app/apps/file_hosting/user_card/company.csv')

    @task
    def fishretail_loader():
        """Выгрузка данных из таблицы fishretail_userprofile
        """
        fishretail = pd.DataFrame(create_fishretail(), columns=MEAT_FISH_COLUMNS)
        fishretail.to_csv(
            '/app/apps/file_hosting/user_card/fishretail.csv')

    @task
    def last_date_loader():
        """Выгрузка данных о последней активности пользователя
        """
        last_df = pd.DataFrame(create_last_date(), columns=LAST_DATE_COLUMNS)
        last_df.to_csv(
            '/app/apps/file_hosting/user_card/last_date.csv')

    @task
    def meatinfo_loader():
        """Выгрузка данных из таблицы meatinfo_userprofile
        """
        meatinfo = pd.DataFrame(create_meatinfo(), columns=MEAT_FISH_COLUMNS)
        meatinfo.to_csv(
            '/app/apps/file_hosting/user_card/meatinfo.csv')

    @task
    def regions_loader():
        """Выгрузка данных из таблицы geobaza_region
        """
        regions = pd.DataFrame(create_regions(), columns=REGION_COLUMNS)
        regions.to_csv(
            '/app/apps/file_hosting/user_card/regions.csv')

    @task
    def user_stat_loader():
        data = create_user_stat()
        df = pd.DataFrame(data, columns=USERSTAT_COLUMNS)
        df = df[df.type != 'search']
        df.loc[df.type2 == '', 'type2'] = '1'
        path = '/app/apps/file_hosting/user_card/userStat.csv'
        df.to_csv(path)
        return path

    add_task = add_date_loader()
    company_task = company_loader()
    fish_task = fishretail_loader()
    last_task = last_date_loader()
    meat_task = meatinfo_loader()
    regions_task = regions_loader()
    user_stat_task = user_stat_loader()
    # pylint: disable=pointless-statement
    add_task >> company_task >> fish_task >> last_task >> meat_task >> regions_task >> user_stat_task

user_card_preparer()
