"""
Валидатор имен
"""
import json
import random

from flask import request, render_template

from . import blueprint
from .detect_product import DetectProductRuBERT
from .dataset import load_text_val

# длина текста
MAX_LENGTH = 15


@blueprint.route("/product/", methods=['GET'])
def index():
    """
    Страница определения продукции
    """
    return render_template("index.html")


@blueprint.route('/product/product-detect', methods=['POST'])
def product_detect():
    """
    Определение продукции
    """
    text = request.form.get('text')
    model = request.form.get('model')

    detect_product = DetectProductRuBERT(model, MAX_LENGTH)
    detect_product.load()
    result = detect_product.detect(text)

    return json.dumps(result, ensure_ascii=False).encode('utf8')


@blueprint.route('/product/test-text', methods=['POST'])
def test_text():
    """
    Получить случайный образец из тестовой выборки
    """
    text_val = load_text_val()
    result = text_val[random.randint(0, len(text_val) - 1)]
    return json.dumps(result, ensure_ascii=False).encode('utf8')
