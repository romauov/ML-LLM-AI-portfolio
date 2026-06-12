"""
Квалификатор ответов 

@author Dmitry Abramov
"""
import os
import sys

import numpy as np
from flask import Blueprint


sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('answer_validator', __name__)

CLASSES = np.array([
    'встречное предложение (комплиментарное)',
    'встречное предложение (некомплиментарное)',
    'запрос конкретной продукции', 
    'запрос прайса',
    'отказ', 'спам',
    'уточнение информации'
    ])

CLASSES_CODES = {
    'встречное предложение (комплиментарное)': 0,
    'уточнение информации': 1,
    'встречное предложение (некомплиментарное)': 2,
    'запрос прайса': 3,
    'запрос конкретной продукции': 4,
    'спам': 5,
    'отказ': 7
    }

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
