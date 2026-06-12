"""
Рекомендации на основе ближайшего соседа

Pipeline работает с таблицами спам и конкуренты m16

@author Dmitry Abramov
"""
from datetime import datetime
import gc
import time

from sentry_sdk import capture_message
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors

from lib.user_stat_db import user_stat, email_db
from lib.tsop_maillists import tsop_maillisted_users, spamers
from buyers_definition.config import ADMIN_USERS, USERSTAT_COLUMNS


# pylint: disable=too-many-arguments
# pylint: disable=too-few-public-methods
class ReccomendationPipeline:
    """
    Система рекомендаций на основе метода ближайшего соседа, для меры схожести используется
    косинусное расстояние
    """
    def __init__(self):
        self.user_stat = None
        self.ratios = None
        self.user_emails = None
        self.note = ""
        # self.p_groupes = (0.65, 0.25, 0.1)

    def pipeline(self, product: str, number_of_users: int, tsop_id: int):
        """
        Pipeline для системы рекомендаций на основе метода ближайшего соседа

        Pipeline состоит из нескольких основных компонентов:
            1. Подготовка данных:
                1. Объединение type1 и type2 в один продукт
                2. Приведение к нижнему регистру продукции
                3. Расчет взаимодействия пользователя с продуктом
                4. Построение сводной таблицы, пропуски которой заполняются нулями
            2. Построение модели ближайшего соседа для идентификации 3 похожих продуктов
            3. Фильтрация пользователей:
                а. По последней активности на сайте
                b. Удаление игнорщиков/спамеров
                c. Удаление пользователей, которые редко взаимодействуют с продукцией(type1)
            4. Построение списков:
                a. Списки строятся на основе краткосрочных интересов, если количество найденных пользователей 
                    меньше целевого - увеличивается период поиска
                b. В первую очередь отбираются пользователи, которые работают с целевым продуктом(указанным в запросе), 
                    затем с продукцией, которую определила модель
                c. Если количество пользователей меньше целевого, производится отбор пользователей, 
                    которые работали с type1

        Принимает:
            product: str - Искомый продукт (type1 + " " + type2 - вид мяса и разруб, например Говядина блочная)
            number_of_users: int Количество пользователей, которое должно быть в списке
        Возвращает:
            json следующего формата:
            json({"emails": ["alexandr3911@gmail.com", "kirpikov_78@mail.ru"],
                  "userIds": [267775, 15115]})
            В случае возникновения ошибки, когда невозможно построить список по type1:
                json({"error": "type1='Собачело' не найден"})
        """
        # Выгрузка данных
        start = time.time()
        self._read_dataframes()
        capture_message(f'Время на чтение данных из бд: {time.time() - start}', 'info')
        capture_message(f'Размерность userStat: {self.user_stat.shape}', 'info')
        capture_message(f'Размерность emails: {self.user_emails.shape}', 'info')
        capture_message(f'Количество уникальных пользователей в userStat: {self.user_stat.userId.nunique()}', 'info')
        start = time.time()
        self.ratios = self._product_ratio(product)
        capture_message(f'Время на ratios: {time.time() - start}', 'info')
        capture_message(f'Размерность ratio: {self.ratios.shape}', 'info')
        sended_emails = self._maillisted_users(tsop_id)
        spam_users = self._spamers()

        start = time.time()
        frame = self._recomendation(product.lower())
        capture_message(f'Время на построение рекомендаций: {time.time() - start}', 'info')
        capture_message(f'Размерность frame до фильтрации: {self.ratios.shape}', 'info')
        if isinstance(frame, str):
            return {"error": f"type1='{product}' не найден"}

        start = time.time()
        frame = self._sort_ouput(frame, number_of_users, sended_emails, spam_users)
        capture_message(f'Время на на фильтрацию: {time.time() - start}', 'info')
        capture_message(f'Размерность frame после фильтрации: {frame.shape}', 'info')

        start = time.time()
        frame = self._sampling(frame, number_of_users)
        capture_message(f'Время на на отбор пользователей: {time.time() - start}', 'info')
        capture_message(f'Размерность frame после семплирования: {frame.shape}', 'info')


        if len(frame) < number_of_users and frame.shape[1] <= 5:
            start = time.time()
            added_users = self._adding_users(frame.userId.tolist(),
                                             number_of_users - len(frame), product,
                                             sended_emails,
                                             spam_users)
            frame = pd.concat([frame, added_users])
            print(added_users.userId.values)
            capture_message(f'Время на на добавление пользователей: {time.time() - start}', 'info')

        frame = frame.drop_duplicates(subset=['userId'])
        capture_message(f'Размерность frame после удаления дубликатов: {frame.shape}', 'info')
        # Освобождение памяти
        self.user_stat = None
        self.ratios = None
        self.user_emails = None
        gc.collect()
        note = self.note
        self.note = ""
        return frame.email.tolist(), frame.userId.tolist(), note

    def _read_dataframes(self):
        """
        Выгрузки userStat и статистики открытия рассылок из БД
        """
        data = user_stat()
        data = pd.DataFrame(data, columns=USERSTAT_COLUMNS)
        # Удаление администраторов
        self.user_stat = data[~data['userId'].isin(ADMIN_USERS)]

        data = email_db()
        data = pd.DataFrame(data, columns=['userId', 'email'])
        self.user_emails = data[~data['userId'].isin(ADMIN_USERS)]

    def _recomendation(self, product: str):
        """
        Построение списка пользователей, которые могут быть заинтересованы в продукции

        В случае отсутствия переданного продукта, поиск пользователей осуществляется по первому слову(type1),
        например: получено - "Говядина шоколадная", будут отобраны пользователи, которые взаимодействовали
        с любым разрубом Говядины

        Если взаимодействующих пользователей с продукцией оказывается мало (менее 100) - поиск осуществляется по type1.
        Например, для "Гусь Итальянский", будет поиск по продукции "Гусь". Такой подход позволяет сократить количество
            неправильных рекоменаций. 

        Принимает:
            product: str -  Искомый продукт (type1 + " " + type2 - вид мяса и разруб, например Говядина блочная)
        Возвращает pd.DataFrame(), где index - userId, columns - продукты, DataFrame заполнен 0 и 1, 1 - пользователь
            взаимодействовал с продукцией, 0 - нет

        Если невозможно найти продукцию (type1 + " " + type2 - вид мяса и разруб, например Говядина блочная), 
            поиск пользователей будет осуществляться по type1, если type1 отсутствует в таблице - возвращается 
            сообщение "type1 не найден"
        """
        # Подготовка данных для построения модели
        frame = self._prepare_data(self.user_stat)

        try:
            prediction = self._fit(frame, product)
            codes = dict(enumerate(frame.index.values))
            list_of_recommendation = [codes[product] for product in prediction[0].tolist()]
            rec_frame = frame.T[list_of_recommendation]

        except KeyError:
            list_of_recommendation = np.array([_product.split()[0] for _product in frame.index.values])
            list_of_recommendation = np.argwhere(list_of_recommendation == product.split()[0].lower()).reshape(-1)
            rec_frame = frame.T.iloc[:, list_of_recommendation]
            self.note += "Поиск выполнялся по type1 (продукт не был найден). "

        if len(rec_frame[rec_frame != 0].dropna(how='all')) < 100 and rec_frame.shape[1] != 0:
            list_of_recommendation = np.array([_product.split()[0] for _product in frame.index.values])
            list_of_recommendation = np.argwhere(list_of_recommendation == product.split()[0].lower()).reshape(-1)
            rec_frame = frame.T.iloc[:, list_of_recommendation]
            self.note += "Поиск выполнялся по type1 (из-за нехватки пользователей). "
        elif rec_frame.shape[1] == 0:
            return "type1 не найден"

        rec_frame = rec_frame[rec_frame != 0].dropna(how='all')
        rec_frame = rec_frame[rec_frame.index.isin(self.ratios[self.ratios.type1_ratio > 0.1].userId)]
        return rec_frame

    def _fit(self, table, product):
        """
        Настройка алгоритма ближайшего соседа на основе косинусного расстояния и 20 соседей
        Алгоритм ищет похожую на запрашиваемую продукцию и возвращает 3 похожих продукта

        Принимает: 
            table: pd.DataFrame - сводная таблица взаимодействий пользователей с разной продукцией
            product: str - Продукт, по которому строится рекомендация
        """
        model = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)
        model.fit(table)
        neighbors = model.kneighbors(table.loc[product].values.reshape(1, -1), 3, return_distance=False)
        return neighbors

    def _prepare_data(self, df):
        """
        Подготовка данных:
            1. Объединение type1 и type2 в один продукт
            2. Приведение к нижнему регистру продукции
            3. Расчет взаимодействия пользователя с продуктом
            4. Построение сводной таблицы, пропуски которой заполняются нулями
        """
        copy_df = df.copy()
        # Продукты
        copy_df['product'] = copy_df['type1'] + ' ' + copy_df['type2']
        copy_df['product'] = copy_df['product'].map(lambda x: str(x).lower())
        # Расчет взаимодействий для каждого пользователя
        copy_df = copy_df[['userId', 'product']].value_counts(normalize=True).reset_index(name='count')
        # Округление до 1
        copy_df['count'] = np.ceil(copy_df['count'])
        copy_df = copy_df[copy_df['product'] != ' ']
        # Заполнение нулями пропущенных значений в сводной таблице
        product_pivot = copy_df.pivot(index='product',
                                      columns='userId',
                                      values='count').fillna(0)
        capture_message(f'размер сводной таблицы: {product_pivot.shape}', 'info')
        del copy_df
        return product_pivot

    def _sort_ouput(self, df, number_of_users, sended_emails, spamers_emails):
        """
        Фильтрация пользователей по последним действиям, открытиям рассылки, удаление спамеров

        В первую очередь берутся пользователи, которые взаимодействовали с продукцией недавно, 
            окна для поиска: [7, 14, 30, 120, 180] дней
        """
        output = df.copy()
        output = pd.merge(output.reset_index(), self.user_emails, on='userId')
        output = output[(~output.email.isin(sended_emails.email)) &
                        (~output.email.isin(spamers_emails.email))]
        # Периоды поиска
        periods = [7, 14, 30, 120, 180]

        # Дата последнего действия пользователя
        last_actions = self.user_stat[self.user_stat.userId.isin(output.userId)].sort_values('date')\
                                     .drop_duplicates(subset=['userId'], keep='last')[['userId', 'date']]
        last_actions.date = pd.to_datetime(last_actions.date).dt.date
        for period in periods:
            last_action = last_actions[datetime.now().date() - last_actions.date < pd.Timedelta(period, 'D')].copy()
            if len(last_action) >= number_of_users:
                break
        self.note += f"Пользователи отобраны за {period} дневный период. "
        capture_message(f'Период, по которому отобрались пользователи: {period}', 'info')
        capture_message(f'last_action shape: {last_action.shape}', 'info')
        capture_message(f'last_action userId nunique: {last_action.userId.nunique()}', 'info')

        capture_message(f'output shape до сортировки: {output.shape}', 'info')
        output = output[output.userId.isin(last_action.userId)]
        capture_message(f'output shape после сортировки: {output.shape}', 'info')
        return output.drop_duplicates(subset=['userId'])

    def _sampling(self, frame, number_of_users):
        """
        Выбор пользователей

        Принимает: 
            frame: pd.DataFrame, таблица взаимодействий пользователей с разной продукцией,
                пример датафрейма: 
                {'userId': [234212],
                 'говядина полутуши': [1],
                 'говядина блочная': [0],
                 'говядина мясо': [1], 
                 'email': ['vasya228.rush.killer@mail.ru']}
            number_of_users: int - Количество пользователей, которое должно быть в списке
        Возвращает:
            pd.DataFrame
        """
        groupes = pd.DataFrame()

        for index in range(frame.shape[1] - 1):
            if len(groupes) >= number_of_users:
                return groupes
            group = frame[(frame.iloc[:, index+1] == 1) &
                          (~frame.index.isin(groupes.index))].copy()
            group = group.sample(number_of_users - len(groupes)\
                                 if len(group) > number_of_users - len(groupes)\
                                 else len(group),
                                 replace=False)
            groupes = pd.concat([groupes, group])
            capture_message(f'group shape {group.shape}, продукт:{frame.columns[index+1]}', 'info')

        # for index, _p in enumerate(self.p_groupes):
        #     group = frame[(frame.iloc[:, index+1] == 1) &
        #                   (~frame.index.isin(groupes.index))]
        #     group = group.sample(int(number_of_users * _p) if len(group) > number_of_users * _p else len(group),
        #                          replace=False)
            # groupes = pd.concat([groupes, group])
        return groupes

    def _adding_users(self, user_ids, target_number, product, sended_emails, spamers_emails):
        """
        Выбор пользователей

        Принимает: 
            user_ids: list - уже выбранные id пользователей
            target_number: int - Количество пользователей, которое нужно добавить в список
            product: продукт, по которому осуществляется поиск, для поиска используется первое слово (type1),
                например, передано: "Гусь Итальянская", поиск осуществляется среди всех пользователей, 
                которые взаимодействовали с "Гусь"
        """
        df = self.user_stat.copy()

        type1 = product.split()[0].title()

        periods = [7, 14, 30, 120, 180]

        df = df[(df.type1 == type1) &
                (~df.userId.isin(user_ids)) &
                (df.userId.isin(self.ratios[self.ratios.type1_ratio > 0.3].userId))]

        last_actions = df.sort_values('date')\
                    .drop_duplicates(subset=['userId'], keep='last')[['userId', 'date']]
        last_actions.date = pd.to_datetime(last_actions.date).dt.date

        last_action = pd.merge(last_actions, self.user_emails, on='userId')
        last_action = last_action[(~last_action.email.isin(sended_emails.email)) &
                                  (~last_action.email.isin(spamers_emails.email))]

        for period in periods:
            last_action = last_actions[datetime.now().date() - last_actions.date < pd.Timedelta(period, 'D')].copy()
            if len(last_action) >= target_number:
                break

        target_number = len(last_action) if len(last_action) < target_number else target_number
        return last_action.sample(target_number, replace=False)

    def _maillisted_users(self, tsop_id):
        """
        Возвращает список пользователей, которые получали рассылки от клиента ЦОПА в течение 
        последних двух недель
        """
        email = tsop_maillisted_users(tsop_id)
        email = pd.DataFrame(email, columns=['email'])
        capture_message(f'Количество пользователей, получавших сообщения от клиента: {len(email)}', 'info')
        capture_message(f'Первая строка датафрейма:\n{email.head(1)}', 'info')
        return email

    def _spamers(self):
        """
        Возвращает список пользователей, которые получали рассылки от клиента ЦОПА в течение 
        последних двух недель
        """
        email = spamers()
        email = pd.DataFrame(email, columns=['email'])
        capture_message(f'Количество конкурентов, отписавшихся: {len(email)}', 'info')
        capture_message(f'Первая строка датафрейма:\n{email.head(1)}', 'info')
        return email

    def _product_ratio(self, product):
        """
        Относительное количество действий с type1 для пользователя

        Например, пользозователь с userId 100 имеет следующие взаимодействия с type1: 
            ['Говядина', 'Говядина', 'Свинина', 'Говядина']
        Для него относительное количество действий с говядиной равно 0.75
        """
        df = self.user_stat.copy()
        type1 = product.split()[0].title()
        ratios = df[df.userId.isin(df[df.type1 == type1].userId)].groupby('userId')\
                    .agg(type1_ratio=('type1', lambda x: x.value_counts().loc[type1] / len(x))).reset_index()
        return ratios
