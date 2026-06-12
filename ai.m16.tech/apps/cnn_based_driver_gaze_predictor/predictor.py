"""
Загрузка и обработка изображения водителя для определения направления взгляда

Вызов происходит в routes.py

@author Sergey Vakhrameev
"""
import os
from urllib.parse import urlencode

import numpy as np
import torch
import torch.nn.functional as nnf
import torchvision
import mtcnn
import cv2
from PIL import Image
import requests


class Predictor:
    """
    Предиктор направления взгляда
    """
    def __init__(self):
        self.device = 'cpu' # torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.face_detector = mtcnn.MTCNN()
        self.gaze_tracker = self.load_gaze_tracker('data/models/enet_b0_sota.pt')
        self.decode_target = {
            0: 'upper left part of the windshield', # 'левая верхняя часть лобового стекла',
            1: 'straight', # 'прямо перед собой',
            2: 'speedometer', #'спидометр',
            3: 'radio', # 'радио',
            4: 'upper right part of the windshield', #'правая верхняя часть лобового стекла',
            5: 'bottom right part of the windshield', #'правая нижняя часть лобового стекла',
            6: 'right side mirror', #'правое боковое зеркало',
            7: 'rear view mirror', #'зеркало заднего вида',
            8: 'left side mirror', #'левое боковое зеркало',
        }


    def load_image(self, image_path: str):
        """
        Загрузка изображения из Яндекс Диска
        """
        base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'

        # Получаем загрузочную ссылку
        final_url = base_url + urlencode({"public_key": image_path})
        response = requests.get(final_url, timeout=10)
        download_url = None

        try:
            download_url = response.json()['href']
            # Загружаем файл и сохраняем его
            image = Image.open(requests.get(download_url, stream = True, timeout=10).raw)
            image = np.array(image)
        except KeyError:
            image = {'error': 'Доступ к файлу закрыт'}

        return image


    def load_gaze_tracker(self, model_path: str):
        """
        Загрузка модели для определения направления взгляда
        """
        cur_dir, _ = os.path.split(os.path.realpath(__file__))
        model_path = os.path.join(cur_dir, model_path)

        model = torch.load(model_path, map_location = torch.device('cpu'))
        # происходит перенос модели на GPU если имеется к нему доступ
        if self.device == 'cuda:0':
            model.to(self.device)
        # переключение модели на режим работы "инференс"
        model.eval()
        return model


    def track_gaze(self, image_path):
        """
        Определение направления взгляда
        """
        # загрузка изображение
        frame = self.load_image(image_path)
        if isinstance(frame, dict):
            return frame

        # конвертация цветовой гаммы изображения для подачи его в модель извлечения лиц
        # frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # извлечение лиц
        bounding_boxes = self.face_detector.detect_faces(frame)
        if len(bounding_boxes) == 0:
            return {'error': 'На изображении лицо не найдено. Попробуйте другое изображение'}

        x, y, width, height = bounding_boxes[0]['box']
        # сохранение лица
        face = frame[y:y+height,x:x+width,:]
        # необходимые преобразования для модели
        transform = torchvision.transforms.Compose(
            [
                torchvision.transforms.ToTensor(),
                torchvision.transforms.Resize((260, 260)),
                # torchvision.transforms.RandomHorizontalFlip(p=1),
                # torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                            # std=[0.229, 0.224, 0.225])
            ]
        )

        face_transformed = transform(face)
        # повышение размерности изображения для избежания ошибки
        face_transformed = torch.unsqueeze(face_transformed, 0)
        # лицо переносится на GPU при наличии к нему доступа
        if self.device == 'cuda:0':
            face_transformed.to(self.device)
        # получение предсказания модели
        predicted_gaze_direction = self.gaze_tracker(face_transformed)

        probs = nnf.softmax(predicted_gaze_direction, dim=1) # .topk(9, dim = 1)
        probs = np.around(probs[0].detach().numpy(), decimals = 2) # frame
        # формирование словаря для преобразования в json
        probs_dict = {}
        for i, prob in enumerate(probs):
            probs_dict[self.decode_target[i]] = str(prob)

        return probs_dict
