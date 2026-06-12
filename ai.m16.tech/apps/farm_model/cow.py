"""
Модель коровы

@author Dmitry Abramov
"""
import numpy as np

from .delivery import Deliver

# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-arguments
class Cow(Deliver):
    """
    Модель коровы

    Корова может давать молоко, отеливаться, умирать при достижении 15 лет
    """
    def __init__(self,
                 age,
                 status='Не рожала',
                 month_deliver=0,
                 cow_milk=0,
                 month_since_last_birth=0,
                 delivery_risk=0.9,
                 conception_risk=0):
        """
        Конструктор класса
        """
        super().__init__()
        self.age = age # Возраст коровы
        self.month = 0 # Месяц логирования
        self.month_deliver = month_deliver
        self.cow_milk = cow_milk
        self.status = status
        self.month_since_last_birth = month_since_last_birth
        self.delivery_risk = delivery_risk
        self.conception_risk = conception_risk

    def udoi(self):
        """
        Месячный удой
        """
        # pylint: disable=no-else-return
        if (self.cow_milk == 1 and self.status in ["Родился", "Отел"]):
            udois =  16.5 + 4 * abs(np.random.randn(30))
            return udois.sum()
        else:
            return 0

    def log_age(self):
        """
        Увеличение возраста на год
        """
        self.age += 1

        # При достижении 15 лет корова умирает
        if self.age >= 15:
            self.age = 100

    def log_month(self):
        """
        Месяц жизни коровы
        """
        # Смерть коровы
        # pylint: disable=no-else-return
        if self.age == 100:
            return 0
        else:
            super().deliver(self.age)
            self.month += 1

            if self.month % 12 == 0:
                self.log_age()

            return self.udoi()
