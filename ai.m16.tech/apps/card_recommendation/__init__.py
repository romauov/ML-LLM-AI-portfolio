"""
Рекомендации для подбора релевантных клиентов на основе портрета пользователя

@author Marat Ibatullin
"""
import os
import sys

from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('card_recommendations', __name__)

DATA_FOLDER = "apps/file_hosting/card_recommendations"

EMBED_DICT = {
        "meatinfo": [DATA_FOLDER + '/df_cards_meatinfo.csv', 
                     DATA_FOLDER + '/embeddings_meatinfo.csv',
                     ],
        "fishretail": [DATA_FOLDER + '/df_cards_fishretail.csv', 
                       DATA_FOLDER + '/embeddings_fishretail.csv',]
}

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
