"""
Загрузка и обработка изображения для отслеживания угла поворота 
головы человека на изображении по осям x и y, а также коэффициента
открытия глаз

Вызов происходит в routes.py

@author Sergey Vakhrameev
"""
import math

import cv2
import mediapipe as mp
import numpy as np


class HeadController():
    """
    Класс для отслеживания угла поворота головы человека на изображении 
    по осям x и y.
    """
    def __init__(self):
        self.right_eye_indexes = [33, 133, 145, 159] # порядок важен
        self.left_eye_indexes = [263, 362, 374, 386] # порядок важен
        self.face_indexes = [33, 263, 1, 61, 291, 199]
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.drawing_spec = mp.solutions.drawing_utils.DrawingSpec(thickness=1, circle_radius=1)

    def get_euclaidean_distance(self, point, point1):
        """
        Вычисление Евклидова расстояния
        """
        x_1, y_1 = point
        x_2, y_2 = point1
        e_distance = math.sqrt((x_2 - x_1)**2 + (y_2 - y_1)**2)
        return e_distance

    def get_blink_ratio(self, img, right_eye_coords, left_eye_coords):
        """
        Метод для определения коэффициента, определяющего степень открытия глаза.
        Коэффициент вычисляется как среднее между отношениями длин между 
        горизонтальной и вертикальной линиями каждого глаза.
        Длина между линиями вычисляется по формуле Евклидова расстояния.
        """
        # точки для построения горизонтальной линии на правом глазу
        rh_right = right_eye_coords[0] # 33 индекс
        rh_left = right_eye_coords[1] # 133 индекс

        # точки для построения вертикальной линии на правом глазу
        rv_top = right_eye_coords[3] # 159 индекс
        rv_bottom = right_eye_coords[2] # 145 индекс

        # отрисовка линий на правом глазу
        cv2.line(img, rh_right, rh_left, (0, 0, 255), 2)
        cv2.line(img, rv_top, rv_bottom, (0, 0, 255), 2)

        # точки для построения горизонтальной линии на левом глазу
        lh_right = left_eye_coords[1] # 362 индекс
        lh_left = left_eye_coords[0] # 263 индекс

        # точки для построения вертикальной линии на правом глазу
        lv_top = left_eye_coords[3] # 386 индекс
        lv_bottom = left_eye_coords[2] # 374 индекс

        # вычисление расстояния между точками
        rh_distance = self.get_euclaidean_distance(rh_right, rh_left)
        rv_distance = self.get_euclaidean_distance(rv_top, rv_bottom)

        lv_distance = self.get_euclaidean_distance(lv_top, lv_bottom)
        lh_distance = self.get_euclaidean_distance(lh_right, lh_left)

        # получение отношения между расстояниями
        re_ratio = rh_distance / rv_distance
        le_ratio = lh_distance / lv_distance

        # усреднение
        ratio = (re_ratio + le_ratio) / 2
        return ratio

    def get_rotation_angles(self, image):
        """
        Вычисление углов поворота головы и коэффициента открытия глаз
        """
        # переворот изображения по горизонтали, конвертация BGR в RGB
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        # lля улучшения точности
        image.flags.writeable = False

        # получение координат лицевых точек
        results = self.face_mesh.process(image)

        # для улучшения точности
        image.flags.writeable = True

        # конвертация изображения из RGB в BGR
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        img_h, img_w, _ = image.shape
        face_3d = []
        face_2d = []

        left_eye_2d = []
        right_eye_2d = []

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # у каждого кадра берем только нужные точки
                for idx, landmark in enumerate(face_landmarks.landmark):
                    if idx in self.face_indexes:
                        x, y = int(landmark.x * img_w), int(landmark.y * img_h)

                        # сохранение 2D координат лицевых точек
                        face_2d.append([x, y])

                        # сохранение 3D координат лицевых точек
                        face_3d.append([x, y, landmark.z])

                    if idx in self.right_eye_indexes:
                        x, y = int(landmark.x * img_w), int(landmark.y * img_h)

                        right_eye_2d.append([x, y])

                    if idx in self.left_eye_indexes:
                        x, y = int(landmark.x * img_w), int(landmark.y * img_h)

                        left_eye_2d.append([x, y])

            # получение коэффициента открытия глаза
            ratio = self.get_blink_ratio(image, right_eye_2d, left_eye_2d)

            face_2d = np.array(face_2d, dtype=np.float64)
            face_3d = np.array(face_3d, dtype=np.float64)

            # фокусное расстояние камеры
            focal_length = 2.2

            # матрицу камеры необходимо составить путем калибровки камеры
            # сейчас установлены значения по умолчанию
            cam_matrix = np.array([ [focal_length, 0, img_h / 2],
                                    [0, focal_length, img_w / 2],
                                    [0, 0, 1]])

            # получение параметров искажения камеры (установлено значение по умолчанию, необходима калибровка)
            dist_matrix = np.zeros((4, 1), dtype=np.float64)

            # оценка ориентации 3D-объекта на 2D-изображении
            _, rot_vec, _ = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)

            # преобразование вектора вращения в матрицу вращения
            rmat, _ = cv2.Rodrigues(rot_vec)

            # получение углов поворота головы
            angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

            y = angles[0] * 360
            x = angles[1] * 360

            ret_dict = {'x_rotation': x, 'y_rotation': y, 'eyes_opening_ratio': ratio}
            return ret_dict

        return {'error': 'Разметка не построена, попробуйте другое изображение'}
