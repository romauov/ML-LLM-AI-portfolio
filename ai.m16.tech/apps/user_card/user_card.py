"""
Cервис для создания карточки пользователя

@author Sergei Romanov
"""
import json
import numpy as np
from jinja2 import Environment, FileSystemLoader
import polars as pl

from .user_card_aux import modify_userstat, show_userstat, modify_tradeboard, show_names_of_ids

# pylint: disable=too-many-branches
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
def create_user_card(site, userid=None, user_email=None):
    """создание карточки пользователя с агрегированной информацией из датасетов:
    1. userStat
    2. tradeboard
    3. meatinfo_userprofile
    4. fishretail_userprofile
    5. user_profile(axe)
    6. catalogue_company
    7. geobaza_region

    Args:
        site (str): meatinfo или fishretail
        userid (int): id пользователя на сайте

    Returns:
        dict: {"user_card": user_card_markdown} с информацией о пользователе,
        его компании, объявлениях и действия связанным с ним на сайте
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

    stat_df = pl.scan_csv('apps/file_hosting/user_card/userStat.csv').with_columns(
        pl.col('userId').cast(pl.Int64, strict=False)).filter(
        (pl.col('userId') == userid) & (pl.col('site') == site)).collect().sort(
            'date', descending=True).to_pandas()
    stats_user = modify_userstat(stat_df, site)

    lead_actions = ['message', 'callButtonTrade', 'comment_trade',
                    'order_from_trade', 'activity_trade', 'activity_profile']
    search_actions = ['watch_sale', 'watch_buy', 'watch_else', 'trade_to_profile_view', 'trade_photo_view']

    trade_df = pl.scan_parquet('apps/file_hosting/cluster_recmndr/tradeBoard.parquet').with_columns(
        pl.col('userId').cast(pl.Int64, strict=False)).filter(
        (pl.col('userId') == userid) & (pl.col('site') == site)).collect().sort('dateModified', descending=True).to_pandas()
    try:
        last_date = pl.scan_csv('apps/file_hosting/user_card/last_date.csv').with_columns(
            pl.col('userId').cast(pl.Int64, strict=False)).filter(
            (pl.col('userId') == userid) & (pl.col('site') == site)
        ).collect().to_pandas()['last_date'].values[0]
    except IndexError:
        last_date = 'информация отсутствует'
    try:
        add_date = pl.scan_csv('apps/file_hosting/user_card/date_add.csv').with_columns(
            pl.col('userId').cast(pl.Int64, strict=False)).filter(
            (pl.col('userId') == userid) & (pl.col('site') == site)
        ).collect().to_pandas()['dateAdd'].values[0]
    except IndexError:
        add_date = 'информация отсутствует'

    tradeboard = modify_tradeboard(trade_df)
    user_trades = tradeboard['ID объявления'].unique()

    top_actions = stats_user['Тип действия'].value_counts().to_markdown()
    buyers_actions = ['create_buy', 'create_up_buy', 'edit_up_buy']
    sellers_actions = ['create_sale', 'create_up_sale', 'edit_up_sale']
    top_products_for_buyers = stats_user.loc[
        ~(stats_user['ID объявления'].isin(user_trades)) & (stats_user['type'].isin(buyers_actions))
        ]['Продукт'].value_counts()[:20]
    top_products_for_sellers = stats_user.loc[
        ~(stats_user['ID объявления'].isin(user_trades)) & (stats_user['type'].isin(sellers_actions))
        ]['Продукт'].value_counts()[:20]
    top_products_watched = stats_user.loc[
        ~(stats_user['ID объявления'].isin(user_trades)) & (stats_user['type'].isin(search_actions))
        ]['Продукт'].value_counts()[:20]

    emails_df = pl.scan_csv('apps/file_hosting/knn_recommendations/user_emails.csv').with_columns(
        pl.col('userId').cast(pl.Int64, strict=False)).filter(
        (pl.col('userId') == userid) & (pl.col('site') == site)).collect().to_pandas()

    if user_email is None:
        user_email = emails_df['email'].values[0]

    company_id = profile_df['company_id'].values[0]

    if np.isnan(company_id):
        company_df = None
    else:
        company_df = pl.scan_csv(
            'apps/file_hosting/user_card/company.csv').with_columns(
                pl.col('id').cast(pl.Int64, strict=False)).filter(
                pl.col('id') == company_id).collect().to_pandas()

    contacts = [
        'phone', 'phone_privacy', 'mobilephone','site', 
        'icq', 'gtalk', 'skype', 'viber', 'whats_app', 'telegram'
        ]
    contact_df = profile_df[contacts].replace('', np.nan)
    user_contacts = contact_df[contact_df.columns[~contact_df.isnull().all()]]

    last_trades = tradeboard[
        ['Дата создания', 'Дата изменения', 'Вид объявления', 'ID объявления', 'Сайт', 'Заголовок', 'Регион объявления']
        ][:10]
    last_trades.loc[:, 'ID объявления'] = last_trades['ID объявления'].apply(
        lambda x: f'[{x}](https://{site}.ru/trade/{x})'
        )
    buy_ads_watched = len(stats_user.loc[
        (stats_user["type"] == "watch_buy") & ~(stats_user["ID объявления"].isin(user_trades))
        ]["ID объявления"].unique())
    sell_ads_watched = len(stats_user.loc[
        (stats_user["type"] == "watch_sale") & ~(stats_user["ID объявления"].isin(user_trades))
        ]["ID объявления"].unique())
    other_ads_watched = len(stats_user.loc[
        (stats_user["type"] == "watch_else") & ~(stats_user["ID объявления"].isin(user_trades))
        ]["ID объявления"].unique())
    buy_ads_posted = len(stats_user.loc[
        (stats_user["type"] == "create_buy") & ~(stats_user["ID объявления"].isin(user_trades))
        ]["ID объявления"].unique())
    sell_ads_posted = len(stats_user.loc[
        (stats_user["type"] == "create_sale") & ~(stats_user["ID объявления"].isin(user_trades))
        ]["ID объявления"].unique())
    other_ads_posted = len(stats_user.loc[
        (stats_user["type"] == "create_else") & ~(stats_user["ID объявления"].isin(user_trades))
        ]["ID объявления"].unique())
    stats_to_user = modify_userstat(
        pl.scan_csv('apps/file_hosting/user_card/userStat.csv').with_columns(
            pl.col('offerId').cast(pl.Int64, strict=False),
            pl.col('userId').cast(pl.Int64, strict=False)).filter(
            (pl.col('offerId').is_in(user_trades)) & (pl.col('site') == site) & (pl.col('userId') != userid)
            ).collect().sort('date', descending=True).to_pandas(), site)
    lead_ids = stats_to_user.loc[stats_to_user['type'].isin(lead_actions)]['userId'].unique()
    watch_ids = stats_to_user.loc[stats_to_user['type'].isin(search_actions)]['userId'].unique()

    usercard_data = {
        'userid': userid,
        'site': site,
        'first_name': profile_df["firstname"].values[0],
        'last_name': profile_df["lastname"].values[0],
        'position': profile_df["position"].values[0],
        'specified_activity': profile_df["activity"].values[0],
        'user_active': len(stats_user) > 0,
        'last_date': last_date,
        'add_date': add_date,
        'user_email': user_email,
        'user_contacts': user_contacts,
        'company_status': not company_df is None,
        'last_trades': last_trades.to_markdown(index=False), 
        'top_actions': top_actions,
        'top_products_for_sellers': top_products_for_sellers,
        'top_products_for_buyers': top_products_for_buyers,
        'top_products_watched': top_products_watched,
        'buy_ads_watched': buy_ads_watched,
        'sell_ads_watched': sell_ads_watched,
        'other_ads_watched': other_ads_watched,
        'buy_ads_posted': buy_ads_posted,
        'sell_ads_posted': sell_ads_posted,
        'other_ads_posted': other_ads_posted,
        'user_lead_actions': show_userstat(stats_user, lead_actions),
        'user_search_actions': show_userstat(stats_user, search_actions),
        'lead_ids': show_names_of_ids(site, lead_ids),
        'leads_to_user': show_userstat(stats_to_user, lead_actions, user_id=True),
        'view_ids': show_names_of_ids(site, watch_ids),
        'searches_to_user': show_userstat(stats_to_user, search_actions, user_id=True)
    }
    user_details = {
        'userid': userid,
        'site': site,
        'first_name': profile_df["firstname"].values[0],
        'last_name': profile_df["lastname"].values[0],
        'position': profile_df["position"].values[0],
        'specified_activity': profile_df["activity"].values[0]
    }

    if company_df is not None:
        try:
            usercard_data['company_title'] = company_df["name_ru"].values[0]
            usercard_data['company_inn'] = company_df["company_inn"].values[0]
            usercard_data['company_description'] = company_df["description_ru"].values[0]
            usercard_data['company_link'] = f'https://{site}.ru/litecat/{company_df["url"].values[0]}'
            usercard_data['company_leader'] = company_df["director_ru"].values[0]
            usercard_data['company_logo'] = company_df["image_id"].values[0]

            user_details['company_title'] = company_df["name_ru"].values[0]
            user_details['company_description'] = company_df["description_ru"].values[0]
        except IndexError:
            pass

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('apps/user_card/template.md')
    user_card = template.render(usercard_data)

    return {"user_card": user_card, "user_details": json.dumps(user_details, ensure_ascii=False)}
