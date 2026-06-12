"""
Словари и другие текстовые данные для обработки мониторингов фруктов
"""

fruit_allowed_names = [
    "ОВОЩИ",
    "ФРУКТЫ,ЯГОДЫ",
    "ОВОЩИ СУШЕНЫЕ  И СУХОФРУКТЫ",
    "ОРЕХИ И КОНСЕРВАЦИЯ",
    "ЗЕЛЕНЬ",
    "ФРУКТЫ"
]

column_mapping = {
    'Округ': 'federal_okrug',
    'Регион / область': 'region',
    'Наименование': 'product',
    'Описание': 'description',
    'Термосостояние': 'temperature_state',
    'Произ-ль': 'country',
    'Вес.уп.': 'batch',
    'Объем': 'volume',
    'Партия': 'packaging',
    'Условие поставки': 'delivery_terms',
    'Цена': 'price',
    'Компания': 'company',
    'Телефон': 'phone',
    'Контакт.лицо': 'contact_person',
    'Наличие': 'availability',
    'E-mail': 'email',
    'Дата': 'date',
}

old_column_mapping = {
    'Страна происхождения': 'Произ-ль',
    'Упаковка': 'Партия',
    'Условия': 'Условие поставки',
    'Контактное лицо': 'Контакт.лицо',
    'Почта': 'E-mail',
}

subfolder_to_okrug = {
    'fruitcentralsushonka': 'ЦФО',
    'fruitcentralsvezhee': 'ЦФО',
    'fruitcentralzamorozka': 'ЦФО',
}

subfolders = ["fruitcentralsushonka", "fruitcentralsvezhee", "fruitcentralzamorozka"]

drop_cols = []

# Папка для файлов с новыми мониторингами
source_folder = '/hosting/new/fruit'
# Папка для успешно обработанных файлов
processed_folder = '/hosting/processed/fruit'
# Папка для файлов с ошибками
errors_folder = '/hosting/errors/fruit'

FRUIT = 'fruit'
