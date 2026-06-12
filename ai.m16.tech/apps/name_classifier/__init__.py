"""
Name classifier
"""
import os
import sys

from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
name_blueprint = Blueprint('name_classifier', __name__)
surname_blueprint = Blueprint('surname_classifier', __name__)

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
