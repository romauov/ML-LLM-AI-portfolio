"""
Module user_card

@author Sergei Romanov
"""
import os
import sys

from flask import Blueprint

COMPANY_COLUMNS = ['id', 'name_ru', 'url', 'company_inn', 'director_ru', 'image_id', 'description_ru']

EMAILS_COLUMNS = ['userId', 'login email', 'site']

MEAT_FISH_COLUMNS = ['user_id', 'firstname', 'lastname', 'company_id', 'position', 'activity',
                     'phone', 'phone_privacy', 'mobilephone', 'mobilephone_privacy', 
                     'site', 'icq', 'gtalk', 'skype', 'viber', 'whats_app', 'telegram']

REGION_COLUMNS = ['id', 'name']

TRADEBOARD_COLUMNS = ['itemId', 'site', 'title', 'userId', 'label', 'regionId', 'dealType',
                      'dateCreated', 'dateModified', 'type1', 'type2', 'category_name']

USERSTAT_COLUMNS = ['userId', 'site', 'userRegion', 'type', 'offerId', 'dealType', 'type1',
                    'type2', 'offerRegion', 'date']

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

blueprint = Blueprint('user_card', __name__)

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
