"""
Трекер времени

@author Dmitry Abramov
"""
import os
import sys

from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('tracker', __name__)
# Номер дня недели
DAYS_OF_WEEK = {
    'Понедельник': 0,
    'Вторник': 1,
    'Среда': 2,
    'Четверг': 3,
    'Пятница': 4,
    'Суббота': 5,
    'Воскресенье': 6
    }
# Словарь для преобразования предсказанного класса в тег
INT2TAG = {9: 'O',
           0: '0',
           1: 'B-DAT',
           2: 'I-DAT',
           3: 'B-MIN',
           4: 'I-MIN',
           5: 'B-TKT',
           6: 'I-TKT',
           7: 'B-PRO',
           8: 'I-PRO'
           }
# Виды работ
TYPE_OF_WORK = {
    0: 'Accounting',
    1: 'Communication',
    2: 'Development',
    3: 'Documentation',
    4: 'Learning',
    5: 'Prototyping',
    6: 'Review',
    7: 'Testing',
    8: '-'
    }
# Месяцы
MONTHS = {
    'январ': '01',
    'феврал': '02',
    'март': '03',
    'апрел': '04',
    'ма': '05',
    'июн': '06',
    'июл': '07',
    'август': '08',
    'сентябр': '09',
    'октябр': '10',
    'ноябр': '11',
    'декабр': '12'
    }

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
