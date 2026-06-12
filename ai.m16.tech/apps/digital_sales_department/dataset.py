"""
Загрузка датасета

@author Sergey Goncharov
"""
import io
import pathlib

import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import TensorDataset

from digital_sales_department.db import user_views_service, users_stat

DIR_DATASET = 'apps/digital_sales_department/data/ds'

# Услуги для продавцов
SERVICES_SELLERS = [290, 337, 121, 122, 379, 409, 364, 399, 427, 350, 288, 387, 242, 436]


def string_to_list(item: str):
    """
    Преобразование строки в список
    """
    if item == '[]':
        return []
    item = item.replace('[', '').replace(']', '').split(',')
    return [int(value) for value in item]


def load_dataset_train():
    """
    Загрузка датасета из файла data/ds/user-stat.csv
    """
    path = DIR_DATASET + '/user-stat.csv'
    df = pd.read_csv(path, sep=';')

    df['payShopList'] = df['payShopList'].map(string_to_list)

    df['target'] = df['payShopList'].apply(lambda x: 1 if len(set(SERVICES_SELLERS).intersection(x)) > 0 else 0)

    user_id_target = df[df['target'] == 1]['userId'].values

    df['target'] = df['userId'].apply(lambda x: 1 if x in user_id_target else 0)

    df = df.drop(columns=[
        'userId',
        'viewShopList',
        'addShopList',
        'payShopList',
        'addShop',
        'position',
        'activity',
    ])

    df_train, df_val = train_test_split(df, test_size=0.2, shuffle=True, random_state=1234)

    target_train = df_train[['target']]

    df_train = df_train.drop(['target', 'payShop'], axis=1)

    df_train = torch.Tensor(df_train.values)
    target_train = torch.Tensor(target_train.values).to(torch.long)

    target_val = df_val[['target']]
    df_val = df_val.drop(['target', 'payShop'], axis=1)
    df_val = torch.Tensor(df_val.values)

    target_val = torch.Tensor(target_val.values).to(torch.long)

    input_site = df_train.shape[1]

    dataset_train = TensorDataset(df_train, target_train)
    dataset_val = TensorDataset(df_val, target_val)

    return dataset_train, dataset_val, input_site


def save_dataset(df: pd.DataFrame):
    """
    Сохранить датасет в файл data/ds/user-stat.csv
    """
    pathlib.Path(DIR_DATASET).mkdir(parents=True, exist_ok=True)
    path = DIR_DATASET + '/user-stat.csv'

    with io.open(path, 'w', encoding='utf-8') as file:
        file.write(df.to_csv(sep=';', index=False))


def load_dataset_from_db():
    """
    Загрузка датасета из базы данных и сохранение в файл
    """
    interval_mounts = 3
    items_list = []
    months_ago = 0
    for _ in range(1, 20):
        months_ago = months_ago + interval_mounts
        items = user_views_service(months_ago, interval_mounts)
        print('size', len(items))
        items_list = items_list + items

    df = pd.DataFrame(data=items_list, columns=[
        'userId',
        'createBuy',
        'createSale',
        'createUpBuy',
        'createUpSale',
        'editUpBuy',
        'editUpSale',
        'watchSale',
        'watchBuy',
        'activityTrade',
        'activityCompany',
        'activityProfile',
        'myOffers',
        'profileView',
        'tradePhotoView',
        'tradeToProfileView',
        'tradeFilter',
        'message',
        'viewCompany',
        'monitoringView',
        'newsView',
        'analyticsView',
        'dynamicsView',
        'viewShop',
        'viewShopUniq',
        'viewShopList',
        'addShop',
        'addShopList',
        'payShop',
        'payShopList',
        'position',
        'activity'
    ])

    save_dataset(df)


def dataset_users(users: list) -> pd.DataFrame:
    """
    Получение статистики пользователей из базы данных

    :param users: id пользователей
    """
    interval = 3

    items = users_stat(users, interval)

    df = pd.DataFrame(data=items, columns=[
        'createBuy',
        'createSale',
        'createUpBuy',
        'createUpSale',
        'editUpBuy',
        'editUpSale',
        'watchSale',
        'watchBuy',
        'activityTrade',
        'activityCompany',
        'activityProfile',
        'myOffers',
        'profileView',
        'tradePhotoView',
        'tradeToProfileView',
        'tradeFilter',
        'message',
        'viewCompany',
        'monitoringView',
        'newsView',
        'analyticsView',
        'dynamicsView',
        'viewShop',
        'viewShopUniq',
    ])

    return df
