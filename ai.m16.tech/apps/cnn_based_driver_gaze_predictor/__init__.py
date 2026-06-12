"""
@author Sergey Vakhrameev
"""
import os
import sys

from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('cnn_based_driver_gaze_predictor', __name__)

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
