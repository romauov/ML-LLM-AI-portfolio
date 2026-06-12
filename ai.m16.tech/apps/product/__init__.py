"""
Name classifier
"""
import os
import sys

from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('product', __name__, template_folder='./templates')

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
