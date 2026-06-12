"""
Функции для создания карточки пользователя

@author Sergei Romanov
"""
import pandas as pd
import polars as pl

def modify_userstat(df, site):
    """Замена названий на русские и добавление ссылок для пользователей и объявлений

    Args:
        df (DataFrame): userStat
        site (str): meatinfo или fishretail

    Returns:
        DataFrame: userStat с русскими названиями и ссылками 
    """
    regions_df = pd.read_csv('apps/file_hosting/user_card/regions.csv', usecols=['id', 'name'])
    df = df.merge(regions_df, left_on='offerRegion', right_on='id', how='left').drop('id', axis=1)

    rename_dict = {
        'activity_profile': 'просмотр контактов профиля',
        'activity_trade': 'просмотр контактов объявления',
        'callButtonTrade': 'звонок по объявлению',
        'comment_trade': 'комментарий объявления',
        'create_buy': 'создание объявления о покупке',
        'create_else': 'создание объявления',
        'create_sale': 'создание объявления о продаже',
        'create_up_buy': 'подъём объявления о покупке',
        'create_up_else': 'подъём объявления',
        'create_up_sale': 'подъём объявления о продаже',
        'edit_up_buy': 'подъём объявления о покупке через редактирование',
        'edit_up_else': 'подъём объявления через редактирование',
        'edit_up_sale': 'подъём объявления о продаже через редактирование',
        'message': 'отправка сообщения',
        'my_offers': 'мои объявления',
        'order_from_trade': 'заказ со страницы объявления',
        'search': 'поиск',
        'watch_buy': 'просмотр объявления о покупке',
        'watch_else': 'просмотр объявления',
        'watch_sale': 'просмотр объявления о продаже',
        'trade_photo_view': 'просмотр фото'
        }

    df.loc[:, 'Тип действия'] = df['type'].apply(lambda x: rename_dict[x])

    df.rename(columns={
        #"userId": "ID пользователя",
        "site": "Сайт", 
        "userRegion": "# региона пользователя", 
        #"type": "Тип действия",
        "offerId": "ID объявления", 
        "dealType": "Вид действия", 
        "type1": "type1", 
        "type2": "type2", 
        "offerRegion": " # региона объявления", 
        "date": "Дата",
        "name": "Регион объявления"
        },
                    inplace=True)

    df = df.merge(regions_df, left_on='# региона пользователя', right_on='id', how='left').drop('id', axis=1)

    df.rename(columns={
        "name": "Регион пользователя"
    },
                    inplace=True)

    df.loc[:, 'Вид действия'] = df['Вид действия'].apply(lambda x: 'покупка' if(x == 'buy')  else 'продажа')

    df['Продукт'] = df['type1'] + ' ' + df['type2']
    df['Действие с продуктом'] = df['Тип действия'] + ' ' + df['Продукт']

    df.loc[:, 'ID пользователя'] = df['userId'].apply(lambda x: f'[{x}](https://{site}.ru/people/view?user={x})')
    df.loc[:, 'ID объявления'] = df['ID объявления'].apply(lambda x: f'[{x}](https://{site}.ru/trade/{x})')

    return df

def show_userstat(df, actions=None, user_id=False):
    """Отображение userStat в markdown в соответствии с фильтром по типу действий

    Args:
        df (DataFrame): userStat
        actions (lst, optional): список действий для фильтрации. Defaults to None.
        id (bool, optional): Отображение id. Defaults to False.

    Returns:
        str: отображение userstat в markdown
    """
    columns_shown = ['Дата', 'ID объявления', 'Вид действия', 'Тип действия',  'Продукт',  'Регион объявления']
    if user_id:
        columns_shown.append('ID пользователя')

    if actions is None:
        result = df.loc[columns_shown].to_markdown(index=False)
    else:
        result = df.loc[df['type'].isin(actions)][columns_shown].to_markdown(index=False)
    return result

def modify_tradeboard(df):
    """_summary_Замена названий на русские и добавление ссылок для объявлений

    Args:
        df (DataFrame): tradeboard

    Returns:
        DataFrame: tradeboard c с русскими названиями и ссылками
    """
    regions_df = pd.read_csv('apps/file_hosting/user_card/regions.csv')[['id', 'name']]
    df = df.merge(regions_df, left_on='regionId', right_on='id', how='left').drop('id', axis=1)
    rename_dict = {
        'buy': 'Покупка',
        'sale': 'Продажа'
    }
    df.loc[:, 'dealType'] = df['dealType'].apply(lambda x: rename_dict[x])
    df.rename(columns={
    'itemId': 'ID объявления', 
    'site': 'Сайт', 
    'title': 'Заголовок', 
    'userId': 'ID пользователя', 
    'label': 'Ярлык', 
    'regionId': 'ID региона', 
    'dealType': 'Вид объявления',
    'dateCreated': 'Дата создания', 
    'dateModified': 'Дата изменения', 
    'type1': 'type1', 
    'type2': 'type2', 
    'category_name': 'Название категории',
    'name': 'Регион объявления'
    },
                inplace=True)

    return df

def show_names_of_ids(site, ids):
    """Отображение имён и фамилий по заданным id

    Args:
        site (str): meatinfo или fishretail
        ids (lst): список id

    Returns:
        str: markdown датафрейма с id, именами и фамилиями
    """
    if site == 'meatinfo':
        df = pl.scan_csv('apps/file_hosting/user_card/meatinfo.csv').filter(
            pl.col('user_id').is_in(ids)).collect().to_pandas()
    else:
        df = pl.scan_csv('apps/file_hosting/user_card/fishretail.csv').filter(
            pl.col('user_id').is_in(ids)).collect().to_pandas()
    df.loc[:, 'user_id'] = df['user_id'].apply(lambda x: f'[{x}](https://{site}.ru/people/view?user={x})')
    df = df[['user_id', 'firstname', 'lastname']]
    df.rename(columns={
    'user_id': 'ID пользователя', 
    'firstname': 'Имя', 
    'lastname': 'Фамилия'
    },
              inplace=True
              )
    return df.to_markdown(index=False)
