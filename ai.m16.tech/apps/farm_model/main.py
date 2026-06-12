"""
Создание фермы

@author Dmitry Abramov
"""
from .farm import Farm
# pylint: disable=too-many-arguments
def farm_modeling(cow_number: int,
                  periods: int,
                  rub_per_litr: float,
                  korm: float,
                  service: float,
                  delivery_risk: float,
                  conception_risk: float):
    """
    Создание фермы

    :params:
        cow_number: int - Количество коров в ферме
        periods: int - Количество месяцев моделирования
        rub_per_litr: float - рублей за литр молока
        korm: float - траты на корм для 1 коровы
        service: float - траты на уход за 1 коровой
    """
    my_farm = Farm(rub_per_litr, korm, service)
    my_farm.model(cow_number, delivery_risk, conception_risk)
    result, ages = my_farm.log_period(periods)
    return result, ages
