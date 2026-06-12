"""
Module chat_helper

@author Sergei Romanov
"""
import os
import sys
from flask import Blueprint

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_PROXY_URL = os.getenv('OPENAI_PROXY_URL', 'https://openai.a505.ru/v1/')
PRICE_ID = os.getenv('PRICE_ID', '')
REGLAMENT_ID = os.getenv('REGLAMENT_ID', '')

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

blueprint = Blueprint('chat_helper', __name__)


# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
