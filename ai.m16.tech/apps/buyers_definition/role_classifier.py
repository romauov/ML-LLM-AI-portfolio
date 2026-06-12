"""
Обработка результата и возврат предсказания
@author Dmitry Abramov
"""
import pickle

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import MinMaxScaler

from lib.user_stat_db import user_stat
from .db import user_mailing_activities
from .config import ADMIN_USERS, MAILING_COLUMNS, USERSTAT_COLUMNS


def diff_time_of_user(dataframe: pd.DataFrame):
    """
        Вычисление среднего количества дней между действиями на сайте
            у пользователя

        Параметры:
            dataframe: pd.DataFrame - набор данных, с которыми работ

        Возвращает:
            dataframe: pd.DataFrame - обработанный набор данных, включающий
                время между действиями
    """
    dataframe = dataframe.drop_duplicates(['userId', 'date'])[['userId', 'date']] \
        .sort_values(by=['userId', 'date'])
    result_array = np.array([])
    # Вычисление времени между активностями на сайте
    for user in dataframe.userId.unique():
        # Смещение выборки для 1 пользователя на 1 строку вниз
        shift_data = dataframe[dataframe.userId == user].date.shift(1)
        # Нахождение разницы, она хранится в списке
        result = dataframe[dataframe.userId == user].date - shift_data
        # Среднее время
        result_array = np.append(result_array, result.mean().round('1d').days)

    # Округление времени до дня
    dataframe.sort_values(by='userId', inplace=True)
    dataframe.drop_duplicates('userId', inplace=True)
    dataframe['date_diff'] = result_array
    dataframe.drop('date', axis=1, inplace=True)
    return dataframe


def delete_admins(df: pd.DataFrame) -> pd.DataFrame:
    """
        Удаление администраторов
    """
    return df[~df.userId.isin(ADMIN_USERS)]


def last_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
        Количество количества дней с последней активности
    """
    # Последняя активность в днях
    last_act = df.groupby('userId')['date'].agg(last_act='max').reset_index()
    last_act['last_act'] = pd.to_datetime(last_act['last_act'])
    # Сегодняшняя дата
    today = pd.to_datetime('today')
    last_act['last_act'] = (today - last_act['last_act']).dt.days

    return df.merge(last_act, on='userId', how='left')


def num_upd_ads(df: pd.DataFrame) -> pd.DataFrame:
    """
        Количество поднятых объявлений
    """

    uped_ads = df[df.type.isin(['create_up_buy', 'create_up_sale',
                                'edit_up_sale', 'edit_up_buy'])] \
        .groupby('userId')['type'].agg(uped_ads='count')
    return df.merge(uped_ads, on='userId', how='left')


def num_created_ads(df: pd.DataFrame) -> pd.DataFrame:
    """
        Количество созданных объявлений
    """

    created_ads = df[df.type.isin(['create_buy', 'create_sale',
                                   'edit_up_sale', 'edit_up_buy'])] \
        .groupby('userId')['type'] \
        .agg(created_ads='count',
             number_of_mode_ad=lambda x: stats.mode(x)[1]) \
        .reset_index()
    return df.merge(created_ads, on='userId', how='left')


def top_3_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
        3 категории мяса, с которыми пользователь взаимодействовал больше всего, и их
        отношение
    """
    request = df.groupby('userId').type1.agg(
        type1_meat1=lambda x: '0' if x.nunique() < 1
        else x.value_counts()[0:1].index,
        type1_meat2=lambda x: '0' if x.nunique() < 2
        else x.value_counts()[1:2].index,
        type1_meat3=lambda x: '0' if x.nunique() < 3
        else x.value_counts()[2:3].index,
        meat1_rate=lambda x: 0 if x.nunique() < 1
        else x.value_counts()[0:1] / x.count(),
        meat2_rate=lambda x: 0 if x.nunique() < 2
        else x.value_counts()[1:2] / x.count(),
        meat3_rate=lambda x: 0 if x.nunique() < 3
        else x.value_counts()[2:3] / x.count(),
    ).reset_index()
    return df.merge(request, on='userId', how='left')


def columns_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    """
        Подготовка столбцов - преобразование в тип datetime
            приведение к нижнему регистру
    """
    # Приведение формата даты-времени
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%m/%d/%Y')
    df['date'] = pd.to_datetime(df['date'])

    # Приведение названий мяса к одному формату
    df['type1'] = df['type1'].map(lambda x: str(x).title())
    return df


def pipeline(date_period: int=90, number_of_users: float=200,
             product: str='Говядина'):
    """
        Конвейер обработки информации о пользователях из userStat

        Параметры:
            path: str - Путь к csv файлу

            date_period: int - Количество дней

            product: list - Интересующие виды мяса

            number_of_users: int - Количество пользователей, по умолчанию
                100

        Возвращает:
            df: Набор данных

    """
    if isinstance(product, list):
        pass
    elif isinstance(product, str):
        product = [product]

    data = user_stat()
    df = pd.DataFrame(data, columns=USERSTAT_COLUMNS)
    # Удаление администраторов
    df = delete_admins(df)
    # Приведение формата даты-времени
    df = columns_preprocessing(df)
    # Добавление колонок в набор данных
    df = top_3_categories(df)
    # Поднятые объявления
    df = num_upd_ads(df)
    # Количество созданных объявлений
    df = num_created_ads(df)
    # Количество дней с последней активности
    df = last_activity(df)

    # Удаление дублирующихся юзер/дата для вычисления активности пользователя
    date_diff_df = df.drop_duplicates(['userId', 'date'])[['userId', 'date']]
    date_diff_df = date_diff_df.sort_values(by=['userId', 'date'])

    df.drop_duplicates('userId', inplace=True)
    df = df[['userId', 'type1_meat1', 'type1_meat2', 'type1_meat3',
             'meat1_rate', 'meat2_rate', 'meat3_rate', 'uped_ads',
             'created_ads', 'number_of_mode_ad', 'last_act']]

    # Отсев по последнему посещению
    df = df[df.last_act < date_period]
    # Выбор необходимого мяса
    df = df[(df['type1_meat1'].isin(product))
            | ((df['type1_meat2'].isin(product))
               & (df['meat2_rate'] >= 0.3))]

    # Если количество пользователей меньше нужного
    if df.userId.count() < number_of_users * 3:
        number_of_users = df.userId.count()
    else:
        number_of_users *= 3

    df.fillna(value=0, inplace=True)

    # Объединение датафреймов
    concated_df1 = df[df['type1_meat1'].isin(product)] \
        [['userId', 'meat1_rate', 'uped_ads',
          'created_ads', 'number_of_mode_ad']] \
        .rename(columns={
        'meat1_rate': 'meat_rate'
    })
    concated_df2 = df[df['type1_meat2'].isin(product)] \
        [['userId', 'meat2_rate', 'uped_ads',
          'created_ads', 'number_of_mode_ad']] \
        .rename(columns={
        'meat2_rate': 'meat_rate'
    })
    df = pd.concat([concated_df1, concated_df2], axis=0)

    # Случайный отбор пользователей
    df = df.sample(number_of_users, replace=False)
    diff_date = diff_time_of_user(date_diff_df[date_diff_df \
                                  .userId.isin(df.userId)])

    df = df.merge(diff_date, on='userId', how='left')

    df.dropna(subset=['date_diff'], axis=0, inplace=True)
    df.fillna(0, inplace=True)
    df['date_diff'] = df['date_diff'].astype('int')

    return df


def normalization(df: pd.DataFrame):
    """
        Предобработка и приведение численных значений к диапазону [0, 1]

        Параметры:
            df: pd.DataFrame - датафрейм, значения которого нужно нормализовать

        Возвращает:
            df: pd.DataFrame - нормализованный датафрейм

    """
    mms = MinMaxScaler()

    df['uped_ads'] = mms.fit_transform(df['uped_ads'].values.reshape(-1, 1))
    df['date_diff'] = mms.fit_transform(df['date_diff'].values.reshape(-1, 1))
    df['created_ads'] = mms.fit_transform(df['created_ads'].values \
                                          .reshape(-1, 1))
    df['number_of_mode_ad'] = mms.fit_transform(df['number_of_mode_ad'].values \
                                                .reshape(-1, 1))
    return df


def predict(df: pd.DataFrame):
    """
        Разметка пользователей с помощью модели бустинга

        Параметры:
            df: pd.DataFrame - набор данных для разметки на покупателей/продавцов

        Возвращает:
            df: pd.DataFrame - набор данных, который включает в себя id,
                уверенность модели и метку
    """
    copy_df = df.copy()
    copy_df = normalization(copy_df)
    # Загрузка модели
    with open('apps/buyers_definition/data/model.sav', 'rb') as file:
        model = pickle.load(file)
    y_pred = model.predict_proba(copy_df.drop('userId', axis=1).values)
    copy_df['label'] = y_pred.argmax(axis=1)
    copy_df['confidence'] = y_pred.max(axis=1)

    return copy_df[['userId', 'confidence', 'label']]


def result_saver(df: pd.DataFrame):
    """
        Сохранение результата, с удалением пользователей,
            которые не читают сообщения
    """
    # Игнорщики
    ignores_data = user_mailing_activities()
    ignores = pd.DataFrame(ignores_data)
    # Переименование колонок
    ignores.columns = MAILING_COLUMNS
    # Отношение открытых рассылок
    ignores['sent_open'] = ignores['open'] / ignores['sent']
    # Преобразование информации после предсказания
    df.label = df.label.replace({1: 'Seller',
                                 0: 'Buyer'})
    df.confidence = df.confidence.round(2)
    y_pred = df.dropna(axis=0)
    y_pred.userId = y_pred.userId.astype('int32')
    # Удаление игнорщиков
    y_pred = y_pred[
        ~y_pred.userId.isin(ignores[ignores['sent_open'] < 0.1].userId)]
    # Получение итоговой выборки
    y_pred = y_pred[
        (y_pred['label'] == 'Buyer') | ((y_pred['label'] == 'Seller')
                                        & (y_pred['confidence'] < 0.65))]
    # Удаление пропущенных значений
    y_pred = y_pred.dropna(axis=0)
    # Сохранение мейлов
    result = ignores.loc[ignores.userId.isin(y_pred.userId), 'email']
    return result


def main(date_period: int, number_of_users: int, product: list):
    """
        Список покупателей
    """
    # Подготовка данных
    prepared_df = pipeline(date_period=date_period,
                           number_of_users=number_of_users,
                           product=product)
    # Предсказание меток
    pred_df = predict(prepared_df)
    # Сохранение
    result = result_saver(pred_df)
    return [{'email': row} for row in result.values.tolist()]
