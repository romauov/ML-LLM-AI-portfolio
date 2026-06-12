"""
Рекомендации на основе ближайшего соседа

Pipeline работает с таблицами спам и конкуренты m16

185 строка: КОСТЫЛЬ: ингредиенты не проходят фильтрацию по взаимодействию с продукцией

@author Dmitry Abramov
"""
from datetime import datetime
import gc
import time

from sentry_sdk import capture_message
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import polars as pl

from . import DATA_FOLDER, PERIODS


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
        self.spamers = None
        self.maillisted_users = None

    def pipeline(self, product: str, number_of_users: int, tsop_id: int, site: str='meatinfo'):
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
        self.read_dataframes(product, tsop_id, site)
        capture_message(f'Время на чтение данных: {time.time() - start}', 'info')
        start = time.time()
        capture_message(f'Размерность userStat: {self.user_stat.shape}', 'info')
        capture_message(f'Первые строки userStat: {self.user_stat}', 'info')
        capture_message(f'Размерность spamers: {self.spamers.shape}', 'info')
        capture_message(f'Размерность maillisted_users: {self.maillisted_users.shape}', 'info')


        start = time.time()
        frame = self._recomendation(product.lower())
        capture_message(f'Размерность frame до фильтрации: {self.ratios.shape}', 'info')
        if not isinstance(frame, str):
            frame, reccomended_products = frame
        else:
            return {"error": f"type1='{product}' не найден"}

        start = time.time()
        frame = self._sort_ouput(frame, number_of_users)
        capture_message(f'Размерность frame после фильтрации: {frame.shape}', 'info')

        start = time.time()
        frame = self._sampling(frame, number_of_users)
        frame = frame.select(pl.col('userId', 'email'))
        capture_message(f'Размерность frame после семплирования: {frame.shape}', 'info')
        if len(frame) < number_of_users and frame.shape[1] <= 5:
            start = time.time()
            added_users = self._adding_users(frame['userId'].to_list(),
                                             number_of_users - len(frame), product)
            frame = pl.concat([frame, added_users])

            capture_message(f'Добавлено пользователей по type1: {len(added_users)}', 'info')
        frame = frame.unique(subset=['userId'])
        capture_message(f'Размерность frame после удаления дубликатов: {frame.shape}', 'info')
        # Освобождение памяти
        self.user_stat = None
        self.ratios = None
        self.user_emails = None
        gc.collect()
        note = self.note
        self.note = ""
        return frame['email'].to_list(), frame['userId'].to_list(), note, reccomended_products

    def read_dataframes(self, product, tsop_id, site):
        """
        Выгрузки userStat и статистики открытия рассылок из БД
        """
        # UserStat
        self.user_stat = pl.read_csv(DATA_FOLDER + 'userStat.csv')\
            .filter(pl.col('site') == site)\
            .drop_nulls(subset=['type1', 'type2'])

        # Адреса пользователей
        self.user_emails = pl.read_csv(DATA_FOLDER + 'user_emails.csv').filter(pl.col('site') == site).drop(['site'])

        # ratios
        self.ratios = pd.read_csv(DATA_FOLDER + 'ratios.csv')
        self.ratios = self.ratios[(self.ratios['type1_product'] == product.split()[0].lower()) &
                                  (self.ratios.site == site)]

        # Получавшие рассылку
        self.maillisted_users = pl.read_csv(DATA_FOLDER + 'maillisted_users.csv')
        self.maillisted_users = self.maillisted_users.with_columns(pl.col('tsop_id').cast(pl.Int64))
        self.maillisted_users = self.maillisted_users.filter(pl.col('tsop_id') == tsop_id)

        # Спам/конкуренты
        self.spamers = pl.read_csv(DATA_FOLDER + 'spamers.csv')

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
        reccomended_products = [product.split()[0]]
        # Подготовка данных для построения модели
        frame = self._prepare_data(self.user_stat)
        try:
            prediction = self._fit(frame, product)
            codes = dict(enumerate(frame.index.values))
            list_of_recommendation = [codes[product] for product in prediction[0].tolist()]
            reccomended_products = list(list_of_recommendation)
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
        rec_frame.index = rec_frame.index.astype('int')
        # КОСТЫЛЬ: ингредиенты не проходят фильтрацию по взаимодействию с продукцией
        if 'ингредиенты' not in product.lower():
            rec_frame = rec_frame[rec_frame.index.isin(self.ratios[self.ratios.type1_ratio > 0.1].userId)]
        return pl.from_pandas(rec_frame.reset_index(names='userId')), reccomended_products

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
        df = self.user_stat.clone()
        df = df.with_columns(product = (pl.col('type1') + ' ' + pl.col('type2')).str.to_lowercase())

        pivot_df = df.group_by(['userId', 'product']).agg(counts=pl.col("product").count())\
            .pivot(values="counts", columns="userId", index="product").clone()

        products = pivot_df['product']

        pivot_df = pivot_df.fill_null(0).select(pl.all().cast(pl.Int32, strict=False))\
                    .with_columns(
                                  pl.when(pl.all() == 0)
                                  .then(pl.all())
                                  .otherwise(1)
                                 )
        pivot_df = pivot_df.with_columns(product = products)
        pd_df = pivot_df.to_pandas().set_index('product')
        del pivot_df
        return pd_df

    def _sort_ouput(self, df, number_of_users):
        output = df.clone()
        output = output.join(self.user_emails, on='userId')
        output = output.filter((~pl.col('email').is_in(self.maillisted_users['email'])) &
                               (~pl.col('email').is_in(self.spamers['email'])))
        last_actions = self.user_stat.filter(pl.col('userId').is_in(output['userId']))\
            .sort('date').unique(subset=['userId'], keep='last').select(pl.col('userId'), pl.col('date'))

        last_actions = last_actions.with_columns(pl.col('date').str.to_datetime("%Y-%m-%d %H:%M:%S").dt.date())
        for period in PERIODS:
            last_action = last_actions.filter(datetime.now() - pl.col('date') < pd.Timedelta(period, 'D'))
            if len(last_action) >= number_of_users:
                break
        self.note += f"Пользователи отобраны за {period} дневный период. "
        output = output.filter(pl.col('userId').is_in(last_action['userId']))
        return output.unique(subset=['userId'])

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
        groupes = pl.DataFrame(schema=frame.schema)
        for index in range(frame.shape[1] - 2):
            if len(groupes) >= number_of_users:
                return groupes

            group = frame.filter((pl.col(frame.columns[index+1]) == 1) &
                                 (~pl.col('userId').is_in(groupes['userId']))).clone()
            group = group.sample(number_of_users - len(groupes)
                                 if len(group) > number_of_users - len(groupes)
                                 else len(group),
                                 with_replacement=False)

            groupes = pl.concat([groupes, group])
            capture_message(f'group shape {group.shape}, продукт:{frame.columns[index+1]}', 'info')
        return groupes

    def _adding_users(self, user_ids, target_number, product):
        """
        Выбор пользователей

        Принимает: 
            user_ids: list - уже выбранные id пользователей
            target_number: int - Количество пользователей, которое нужно добавить в список
            product: продукт, по которому осуществляется поиск, для поиска используется первое слово (type1),
                например, передано: "Гусь Итальянская", поиск осуществляется среди всех пользователей, 
                которые взаимодействовали с "Гусь"
        """
        df = self.user_stat.clone()

        type1 = product.split()[0].title()

        df = df.filter((pl.col('type1') == type1) &
                       (~pl.col('userId').is_in(user_ids)) &
                       (pl.col('userId').is_in(self.ratios[self.ratios.type1_ratio > 0.3]['userId'].tolist()))
                      )

        last_actions = df.sort('date')\
                        .unique(subset=['userId'], keep='last')[['userId', 'date']]
        last_actions = last_actions.with_columns(pl.col('date').str.to_datetime("%Y-%m-%d %H:%M:%S").dt.date())
        last_actions = last_actions.join(self.user_emails, on='userId')
        last_actions = last_actions.filter((~pl.col('email').is_in(self.maillisted_users['email'])) &
                                           (~pl.col('email').is_in(self.spamers['email'])))

        for period in PERIODS:
            last_action = last_actions.filter(datetime.now() - pl.col('date') < pd.Timedelta(period, 'D')).clone()
            if len(last_action) >= target_number:
                break

        target_number = len(last_action) if len(last_action) < target_number else target_number
        return last_action.sample(target_number, with_replacement=False).select(pl.col('userId', 'email'))
