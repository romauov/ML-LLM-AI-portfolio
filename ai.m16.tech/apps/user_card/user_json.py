"""
Cервис для создания json с данными пользователя

@author Sergei Romanov
"""
from json import loads
import pandas as pd
import polars as pl
from .user_card_aux import modify_userstat

# pylint: disable=too-many-branches
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def get_user_data(site, userid=None, user_email=None):
    """получения json с данными пользователя

    Args:
        site (str): meatinfo или fishretail
        userid (int): id пользователя на сайте

    Returns:
        json: данные пользователя
    """
    if userid == 0:
        userid = None
    if user_email == '':
        user_email = None

    if userid is None and user_email is None:
        return {"error": "введите id или эл.почту пользователя"}

    if user_email:
        try:
            id_from_db = pl.scan_csv('apps/file_hosting/knn_recommendations/user_emails.csv').with_columns(
                pl.col('userId').cast(pl.Int64, strict=False)).filter(
                (pl.col('email') == user_email) & (pl.col('site') == site)).collect().to_pandas()['userId'].values[0]
        except IndexError:
            return {"error": "пользователь с указанной эл.почтой не обнаружен"}
        if userid is None:
            userid = id_from_db
        if userid != id_from_db:
            return {"error": "пользователь с указанным id не соответствует указанной эл.почте"}

    if site not in ('meatinfo', 'fishretail'):
        return {"error": "выберите сайт meatinfo или fishretail"}

    if site == 'meatinfo':
        profile_path = 'apps/file_hosting/user_card/meatinfo.csv'

    else:
        profile_path = 'apps/file_hosting/user_card/fishretail.csv'

    profile_df = pl.scan_csv(profile_path).with_columns(
                pl.col('user_id').cast(pl.Int64, strict=False)).filter(
                pl.col('user_id') == userid).collect().to_pandas()

    if len(profile_df) == 0:
        return {"error": "пользователь с указанным id не найден"}

    search_actions = ['watch_sale', 'watch_buy', 'watch_else', 'trade_to_profile_view', 'trade_photo_view']
    lead_actions = ['message', 'callButtonTrade', 'comment_trade',
                    'order_from_trade', 'activity_trade', 'activity_profile']

    stat_df = pl.scan_csv('apps/file_hosting/user_card/userStat.csv').with_columns(
        pl.col('userId').cast(pl.Int64, strict=False)).filter(
        (pl.col('userId') == userid) & (pl.col('site') == site)).collect().sort(
            'date', descending=True).to_pandas()
    stats_user = modify_userstat(stat_df, site)
    if len(stats_user) > 0:
        user_activity = 'active'
        user_activity_details = loads(
            stats_user['Тип действия'].value_counts().reset_index().rename(
                columns = {'Тип действия':'name'}).to_json(orient='records', force_ascii=False))
    else:
        user_activity = 'not active'
        user_activity_details = []

    stats_user_sale = stats_user[stats_user['Вид действия'] == 'продажа']
    product_action_sale_date_end = stats_user_sale[stats_user_sale['type'].isin(lead_actions)]['Дата'].max()
    product_action_sale_date_start = stats_user[stats_user['type'].isin(lead_actions)]['Дата'].min()
    product_action_sale_details = loads(
        stats_user_sale[stats_user_sale['type'].isin(lead_actions)]['Продукт'].value_counts().reset_index().rename(
            columns = {'Продукт':'product'}).to_json(orient='records', force_ascii=False))
    stats_user_buy = stats_user[stats_user['Вид действия'] == 'покупка']
    product_action_buy_date_end = stats_user_buy[stats_user_buy['type'].isin(lead_actions)]['Дата'].max()
    product_action_buy_date_start = stats_user_buy[stats_user_buy['type'].isin(lead_actions)]['Дата'].min()
    product_action_buy_details = loads(
        stats_user_buy[stats_user_buy['type'].isin(lead_actions)]['Продукт'].value_counts().reset_index().rename(
            columns = {'Продукт':'product'}).to_json(orient='records', force_ascii=False))

    stats_user_search = stats_user[stats_user['type'].isin(search_actions)]
    stats_user_search_end = stats_user_search['Дата'].max()
    stats_user_search_start = stats_user_search['Дата'].min()
    stats_user_search_count = stats_user_search.shape[0]
    stats_user_search_sale = stats_user_search[stats_user_search['Вид действия'] == 'продажа']
    stats_user_search_sale_count = stats_user_search_sale.shape[0]
    stats_user_search_sale_products = loads(
        stats_user_search_sale['Продукт'].value_counts().reset_index().rename(
            columns = {'Продукт':'product'}).to_json(orient='records', force_ascii=False))
    stats_user_search_sale_regions = loads(
        stats_user_search_sale['Регион объявления'].value_counts().reset_index().rename(
            columns = {'Регион объявления':'region'}).to_json(orient='records', force_ascii=False))

    stats_user_search_buy = stats_user_search[stats_user_search['Вид действия'] == 'покупка']
    stats_user_search_buy_count = stats_user_search_buy.shape[0]
    stats_user_search_buy_products = loads(
        stats_user_search_buy['Продукт'].value_counts().reset_index().rename(
            columns = {'Продукт':'product'}).to_json(orient='records', force_ascii=False))
    stats_user_search_buy_regions = loads(
        stats_user_search_buy['Регион объявления'].value_counts().reset_index().rename(
            columns = {'Регион объявления':'region'}).to_json(orient='records', force_ascii=False))

    user_json = {
        "activity": {
            "user_activity": user_activity,
            "details": user_activity_details
            },
        "product_action": {
            "sale": {
                "date_start": product_action_sale_date_start,
                "date_end": product_action_sale_date_end,
                "details": product_action_sale_details
                },
            "buy": {
                "date_start": product_action_buy_date_start,
                "date_end": product_action_buy_date_end,
                "details": product_action_buy_details
                }
            },
        "tradeboard_view": {
            "date_start": stats_user_search_start,
            "date_end": stats_user_search_end,
            "count_all": stats_user_search_count,
            "sale": {
                "count": stats_user_search_sale_count,
                "products": stats_user_search_sale_products,
                "regions": stats_user_search_sale_regions
                },
            "buy": {
                "count": stats_user_search_buy_count,
                "products": stats_user_search_buy_products,
                "regions": stats_user_search_buy_regions
                }
            }
        }
    return user_json


def get_company_data(site, company_id):
    """создание json с данными об объявлениях компании и сводкой о её сотрудниках:
    1. userStat
    2. tradeboard
    3. meatinfo_userprofile
    4. fishretail_userprofile
    5. user_profile(axe)
    6. catalogue_company
    7. geobaza_region

    Args:
        site (str): meatinfo или fishretail
        company_id (int): id компании

    Returns:
        dict: {"json_key": json_data} с информацией о компании, объявлениях и действияx связанным с ним на сайте
    """

    if company_id is None:
        return {"error": "введите id или эл.почту пользователя"}

    if site not in ('meatinfo', 'fishretail'):
        return {"error": "выберите сайт meatinfo или fishretail"}

    if site == 'meatinfo':
        profile_path = 'apps/file_hosting/user_card/meatinfo.csv'

    else:
        profile_path = 'apps/file_hosting/user_card/fishretail.csv'

    colleague_ids = pl.scan_csv(profile_path).with_columns(
                    pl.col('company_id').cast(pl.Int64, strict=False)).filter(
                    pl.col('company_id') == company_id
                    ).collect().to_pandas()['user_id'].to_list()
    trade_df = pl.scan_parquet('apps/file_hosting/cluster_recmndr/tradeBoard.parquet').filter(
        (pl.col('userId').is_in(colleague_ids)) & (pl.col('site') == site)
        ).collect().sort('dateModified', descending=True).to_pandas()
    regions_df = pd.read_csv('apps/file_hosting/user_card/regions.csv')[['id', 'name']].rename(
        columns = {'name': 'region_name'})
    trade_df = trade_df.merge(regions_df, left_on='regionId', right_on='id', how='left').drop('id', axis=1)
    trade_df.loc[:, 'product'] = trade_df['type1'] + ' ' + trade_df['type2']
    last_trades = loads(trade_df[['itemId', 'dateModified', 'title', 'product', 'region_name', 'dealType']].rename(
        columns = {'itemId': 'id', 'dateModified': 'date', 'region_name': 'region', 'dealType': 'type'}
        ).to_json(orient='records', force_ascii=False))

    company_json = {
        "last_trade": 
            last_trades,
        "employees": 
            [{'id': i, 'data': get_user_data(site=site, userid=i)} for i in colleague_ids]
    }

    return company_json
