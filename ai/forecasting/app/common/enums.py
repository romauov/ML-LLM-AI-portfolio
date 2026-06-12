from enum import Enum


class ProductsType(Enum):
    meat = 'Мясо'
    seafood = 'Морепродукты'
    caviar = 'Икра'
    fish = 'Рыба'
    shrimp = 'Креветки'
    semiprocessed = 'Полуфабрикаты'


class DateFrequency(str, Enum):
    """
    Частоты данных
    """
    D = "D"
    W = "W"
    W_MON = "W-MON"
    M = "M"
    MS = "MS"
