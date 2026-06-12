"""
Рекомендации на основе ближайшего соседа

@author Dmitry Abramov
"""
import os
import sys

from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('knn_recommenations', __name__)

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
