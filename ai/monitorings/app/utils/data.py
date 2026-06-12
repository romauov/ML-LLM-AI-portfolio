"""
Словари и другие текстовые данные для обработки мониториингов

@author Sergei Romanov
"""
from app.utils.settings import secrets as s

okrug_map = {
    "cfo": "ЦФО",
    "spb": "Санкт-Петербург",
    "szfo": "СЗФО",
    "yfo": "УФО",
    "yufo": "УФО",
    "pfo": "ПФО",
    "ufo": "ЮФО",
    "moscow": "Москва",
    "sfo": "СФО",
    "dv": "ДФО",
    "murmansk": "СЗФО",
}

raw_tables = {
    'meat': s.raw_table_meat,
    'fish': s.raw_table_fish,
    'caviar': s.raw_table_caviar,
    'shrimp': s.raw_table_shrimp,
    'seafood': s.raw_table_seafood,
    'semiprocessed': s.raw_table_semiprocessed,
    'milk': s.raw_table_milk,
    'egg': s.raw_table_egg,
    'fruit': s.raw_table_fruit
}

EXCHANGE_ACTIVITY_TYPES = ['Производитель (Биржа)']
