"""
Рекомендации для подбора релевантных клиентов на основе текста объявлений с использованием bert

@author Marat Ibatullin
"""
import os
import sys

from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('bert_recommendations', __name__)

DATA_FOLDER = "apps/file_hosting/bert_recommendations"

EMBED_DICT = {
        "meatinfo": [DATA_FOLDER + '/embeddings_meatinfo.csv', 
                     DATA_FOLDER + '/embeddings_search_meatinfo.csv',
                     DATA_FOLDER + "/tradeboard.parquet"],
        "fishretail": [DATA_FOLDER + '/embeddings_fishretail.csv', 
                       DATA_FOLDER + '/embeddings_search_fishretail.csv',
                       DATA_FOLDER + "/tradeboard_fish.parquet"]
}


# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
