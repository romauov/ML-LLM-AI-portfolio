"""
Словари и другие текстовые данные для обработки мониторингов яйца
"""

egg_allowed_names = [
    "ЦФО",
    "СЗФО",
    "СФО",
    "УФО",
    "ПФО",
    "ЮФО, СКФО",
]

# Маппинг колонок из Excel в названия для БД
column_mapping = {
    'Округ': 'federal_okrug',
    'Регион': 'region',
    'Категория': 'product_type',
    'Наименование': 'product',
    'Цвет яйца': 'color_egg',
    'Гост/ту': 'gost',
    'Упаковка': 'packaging',
    'Цена': 'price',
    'С ндс / без ндс': 'vat',
    'Компания': 'company',
    'Инн': 'inn',
    'Вид деятельности': 'activity_type',
    'Телефон': 'phone',
    'Контактное лицо': 'contact_person',
    'E-mail': 'email',
    'Дата': 'date',
}

# Подпапки для мониторинга разных регионов
# Пока не известно
subfolders = ["moneggs"]

# Колонки, которые нужно удалить из исходных данных
drop_cols = []

# Папка для файлов с новыми мониторингами
source_folder = '/hosting/new/egg'
# Папка для успешно обработанных файлов
processed_folder = '/hosting/processed/egg'
# Папка для файлов с ошибками
errors_folder = '/hosting/errors/egg'

EGG = 'egg'
