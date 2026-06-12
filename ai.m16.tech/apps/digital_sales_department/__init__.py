"""
@author Sergey Goncharov
"""
import os
import sys

from flask import Blueprint

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
blueprint = Blueprint('digital_sales_department', __name__)

# pylint: disable=cyclic-import
# pylint: disable=wrong-import-position
from . import routes
