"""
Module demo
"""
import os
import sys
from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

blueprint = Blueprint('demo', __name__)

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
