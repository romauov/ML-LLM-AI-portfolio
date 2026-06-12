"""
Базовый класс коровы с функцией отела
другие функции реализованы в надстройке Cow

@author Dmitry Abramov
"""
import numpy as np

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-arguments
class Deliver:
    """
    Роды коровы
    """
    def __init__(self,
                 month_deliver: int=0,
                 month_since_last_birth: int=0,
                 cow_milk: int=0,
                 status: str="Не рожала",
                 delivery_risk: float=0.9,
                 conception_risk: float=0.9):
        self.month_deliver = month_deliver # Месяц положения
        self.month_since_last_birth = month_since_last_birth # Количество месяцев с последних родов
        self.cow_milk = cow_milk # Даёт ли корова молоко
        self.status = status # Положение
        self.delivery_risk = delivery_risk # Шанс успешного рождения
        self.conception_risk = conception_risk # Шанс успешного зачатия

    def _post_deliver_time(self):
        """
        Время после родов
        """
        # После 9 месяцев корова не даёт молоко
        if (self.cow_milk == 1 and self.month_since_last_birth == 9):
            self.cow_milk = 0

        # Теленок родился
        if self.status == "Родился" or self.month_since_last_birth < 12:
            self.month_since_last_birth += 1

        # На следующий месяц после родов статус меняется на отел
        if self.status == "Родился":
            self.status = "Отел"

    def _conception(self, age):
        """
        Зачатие телят
        """
        # Корова уже в положении
        if self.month_deliver and age >= 2:
            self.status = "Зачат"
        elif self.month_since_last_birth and age < 2:
            self.status = "Не рожала"
        # Корова до двух лет не может залететь
        elif self.month_deliver and age < 2:
            self.status = "Не рожала"

        if age < 2:
            return

        if self.cow_milk == 1:
            return

        if self.month_deliver != 0:
            return

        if (self.month_since_last_birth > 10 and self.status == "Отел") \
            or self.status in ["Умер при родах", "Неуспешное зачатие", "Не рожала"]:

            self.status = np.random.choice(["Зачат", "Неуспешное зачатие"],
                                            p=[self.conception_risk,
                                              1-self.conception_risk])
            self.month_deliver = 0

    def deliver(self, age):
        """
        Рождение теленка
        """
        self._post_deliver_time()
        self._conception(age)

        # Рождение теленка
        if self.month_deliver == 9 and self.status == "Зачат":
            self.status = np.random.choice(["Родился", "Умер при родах"],
                                           p=[self.delivery_risk,
                                              1-self.delivery_risk])
            self.month_deliver = 0
            self.month_since_last_birth = 0
            # Неуспешное рождение, корова не даёт молоко
            if self.status == "Умер при родах":
                self.cow_milk = 0
            else:
                self.cow_milk = 1

        # Теленок вынашивается
        elif self.month_deliver < 9 and self.status == "Зачат":
            self.month_deliver += 1
        # После 9 месяцев корова не даёт молоко
        elif self.month_since_last_birth > 9:
            self.cow_milk = 0
