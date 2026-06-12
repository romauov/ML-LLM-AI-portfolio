"""
@author Sergey Vakhrameev
"""
import json

from flask import request

from . import blueprint
from .predictor import Predictor


@blueprint.route('/cnn_based_driver_gaze_predictor', methods=['GET'])
def predict():
    """
    Получение направления взгляда водителя
    """
    # Получение данных
    image_path = request.args.get('image_path', type=str)
    predictor = Predictor()

    # Если ссылка на изображение не введена, возвращается ошибка
    if not image_path:
        return json.dumps({'error': 'Путь не введен'},
                          ensure_ascii=False)

    # Предсказание
    output = predictor.track_gaze(image_path)
    json_array = json.dumps(output, ensure_ascii=False)

    # Возвращение результата
    return json_array
