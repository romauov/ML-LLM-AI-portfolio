"""
Модель фермы 

@author Dmitry Abramov
"""
from datetime import datetime
from collections import Counter

import numpy as np
import pandas as pd
from pandas.tseries.offsets import DateOffset

from .cow import Cow

class Farm():
    """
    Модель фермы
    """
    def __init__(self, rub_per_litr: int, korm: int, service: int):
        self.cows = [] # Список экземпляров класса Корова
        self.rub_per_litr = rub_per_litr # Стоимость литра молока
        self.udois = [] # Удои помесячно
        self.stado = [] # Изменение количества голов в стаде
        self.korm = korm # Стоимость корма в месяц
        self.service = service # Стоимость ухода за коровой в месяц
        self.ages = []

    def model(self, krc_number,
              delivery_risk,
              conception_risk):
        """
        Создание коровок
        """
        self.stado.append(krc_number)
        self.cows = [Cow(age=np.random.randint(2, 15),
                         status='Отел',
                         cow_milk=1,
                         month_since_last_birth=np.random.randint(0, 7),
                         delivery_risk=delivery_risk,
                         conception_risk=conception_risk)
                    if np.random.randint(0, 2) == 1 else
                    Cow(age=np.random.randint(2, 15),
                        month_deliver=np.random.randint(0, 7),
                        delivery_risk=delivery_risk,
                        conception_risk=conception_risk)
                    for i in range(1, krc_number+1)]

    def _income(self, month: int) -> float:
        """
        Доход за месяц

        :params: 
            month: int - месяц, индекс списка
        
        :return:
            Месячная прибыль с продажи молока: float
        """
        return self.udois[month] * self.rub_per_litr

    def _expenses(self) -> float:
        """
        Расходы за месяц

        :return:
            Расходы за месяц: float 
        """

        return (self.korm + self.service) * self.stado[-1]

    def _born_calf(self, cow):
        """
        Рождение теленка

        cow - экземпляр класса, хранящийся в списке self.cows
        """
        if cow.status == "Родился" and np.random.choice([0, 1]) == 1:
            self.cows.append(Cow(age=0))

    def _cow_death(self, cow):
        """
        Регистрация смерти коровы по достижении 15 лет
        """
        if cow.age == 100:
            self.cows.remove(cow)

    def _check_age(self, cow):
        return cow.age

    def _log_month(self):
        """
        Тута прожили коровки месяц
        """
        month_udoi = 0
        ages = []
        for cow in self.cows:
            # Удой всех коров
            month_udoi += cow.log_month()
            # Проверка возраста коровы
            self._cow_death(cow)
            # Рождение теленка
            self._born_calf(cow)
            # Возраст коровы
            ages.append(self._check_age(cow))
        # Добавление удоев в общий учет
        self.udois.append(month_udoi)
        # Подсчет возрастов
        self.ages.append(Counter(ages))

    def log_period(self, period: int) -> pd.DataFrame:
        """
        Моделирование фермерских процессов в течение period месяцев 
        Удой, прибыль, доход, расходы, количество голов
        
        :params:
            period - количество месяцев

        :return:
            Показатели фермы в динамике: pd.DataFrame

        """
        total_income = [0]
        income = [0]
        expenses = []

        for month in range(period):
            self._log_month()
            self.stado.append(len(self.cows))
            total_income.append((self._income(month) - self._expenses()))
            income.append(self._income(month))
            expenses.append(self._expenses())

        ages = pd.DataFrame(self.ages,
                            index=[(datetime.now() + DateOffset(months=x))\
                                   .strftime('%m-%y')
                                   for x in range(len(self.udois))])
        try:
            ages.drop(100, axis=1, inplace=True)
        except KeyError:
            pass
        ages.sort_index(axis=1, inplace=True)
        ages.fillna(0, inplace=True)

        return (pd.DataFrame({'Удой': np.array(self.udois),
                'Чистая_прибыль': np.array(total_income[1:]),
                'Прибыль': np.array(income[1:]),
                'Количество_голов': np.array(self.stado[1:]),
                'Расходы': np.array(expenses)},
                index=[(datetime.now() + DateOffset(months=x)).strftime('%m-%y')
                 for x in range(len(self.udois))]),
               ages)
