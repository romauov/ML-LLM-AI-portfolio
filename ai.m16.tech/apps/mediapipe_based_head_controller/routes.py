"""
@author Sergey Vakhrameev
"""
import json

from flask import request

from cnn_based_driver_gaze_predictor.predictor import Predictor
from . import blueprint
from .inference import HeadController


@blueprint.route('/mediapipe_based_head_controller', methods=['GET'])
def predict():
    """
    Получение углов поворота головы и коэффициента открытия глаз
    """
    # Получение данных
    image_path = request.args.get('image_path', type=str)
    # Загрузка изображения, проверка на тип данных
    image = Predictor().load_image(image_path)
    if isinstance(image, dict):
        return image
    predictor = HeadController()

    # Если ссылка на изображение не введена, возвращается ошибка
    if not image_path:
        return json.dumps({'error': 'Путь не введен'},
                          ensure_ascii=False)

    # Предсказание
    output = predictor.get_rotation_angles(image)
    json_array = json.dumps(output, ensure_ascii=False)

    # Возвращение результата
    return json_array
