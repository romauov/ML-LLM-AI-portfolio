"""
Рекомендации на основе ближайшего соседа

@author Dmitry Abramov
"""
import os
import sys

from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('knn_recommenations_polars', __name__)

DATA_FOLDER = "apps/file_hosting/knn_recommendations/"
PERIODS = [7, 14, 30, 120, 180]

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
