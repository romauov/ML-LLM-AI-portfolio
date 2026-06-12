"""
Веб сервис для создания цифровых карточек

@author Yaroslav Koltashev
"""
import os
import sys

from flask import Blueprint


sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('digital_user_cards', __name__)
# blueprint = Blueprint('digital_user_cards', __name__, template_folder='./templates')

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
