import requests
import time
import unittest
import io
import tempfile
import os

from app.common.settings import secrets as s

API_URL = "http://localhost:81"
BEEF_PRICES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_data/beef_price.xls')
ATTEMPTS = 20

session = requests.Session()
session.auth = (s.api_user, s.api_password)
session.headers.update({
    "Connection": "keep-alive",
})


class TestApiEndpoints(unittest.TestCase):
    """Smoke тесты всех endpoints."""
    data = {
        'sheet_name': 'beef',
        'date_name': 'date',
        'series_name': 'prod',
        'forecasting_steps': 10,
        'year_limit': 10,
        'train_n_epochs': 3,
        'use_only_light_models': False,
        'data_frequency': 'MS',
        'sesoanal_period': 12,
    }

    @classmethod
    def setUpClass(cls):
        with open(BEEF_PRICES_PATH, "rb") as f:
            files = {"file": f}
            response = session.post(f"{API_URL}/predict", files=files, data=cls.data, timeout=300)
            cls.response = response
            cls.task_id = response.json().get('task_id', None)

    def test_submit_task_200_ok(self):
        """/predict"""
        self.assertEqual(
            self.response.status_code,
            200,
            f"Ошибка при отправке задачи: {self.response.text}"
        )

    def test_status_200_ok(self):
        """/status/{task_id}"""
        if self.response.status_code != 200 and not self.task_id:
            self.skipTest("submit task test failed")

        response = session.get(f"{API_URL}/status/{self.task_id}")
        self.assertEqual(response.status_code, 200, f"Ошибка при проверке статуса: {response.text}")

    def test_get_forecasting_result_200_ok(self):
        """/result/{task_id}"""
        if self.response.status_code != 200 and not self.task_id:
            self.skipTest("submit task test failed")

        response = session.get(f"{API_URL}/result/{self.task_id}")
        self.assertEqual(response.status_code, 200, f"Ошибка при получении результата: {response.text}")

    def test_get_forecasting_response_content(self):
        """/result/{task_id} проверка предсказаний"""
        if self.response.status_code != 200 and not self.task_id:
            self.skipTest("submit task test failed")

        for _ in range(ATTEMPTS):
            response = session.get(f"{API_URL}/status/{self.task_id}").json()

            if response["status"] == "SUCCESS":
                result = session.get(f"{API_URL}/result/{self.task_id}").json()
                self.assertEqual(len(result['result']['values']), self.data['forecasting_steps'], )
                return
            elif response["status"] == "FAILURE":
                raise AssertionError("Задача завершена с ошибкой.")
            else:
                print(f"Статус задачи: {response['status']}. Ожидание...")
                time.sleep(10)

        raise AssertionError("Timeout error")


class TestApiValidation(unittest.TestCase):
    """Валидация входных параметров"""

    def test_submit_task_wrong_file_type(self):
        """/predict формат файла с временным рядом"""
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b'some text')
            file = io.BufferedReader(tmp)

            data = {
                'sheet_name': 'beef',
                'date_name': 'date',
                'series_name': 'prod',
                'forecasting_steps': 10,
                'year_limit': 10,
                'data_frequency': 'MS',
                'sesoanal_period': 12,
            }

            response = session.post(f"{API_URL}/predict", files={"file": file}, data=data)
            self.assertEqual(
                response.status_code,
                400,
                f"Статус код отличный от 400 при неправильном sheet_name"
            )

    def test_submit_task_wrong_sheet_name(self):
        """/predict название листа в excel файле"""
        with open(BEEF_PRICES_PATH, "rb") as f:
            data = {
                'sheet_name': 'wrong_sheet',
                'date_name': 'date',
                'series_name': 'prod',
                'forecasting_steps': 10,
                'year_limit': 10,
                'data_frequency': 'MS',
                'sesoanal_period': 12,
            }
            response = session.post(f"{API_URL}/predict", files={"file": f}, data=data)
            self.assertEqual(
                response.status_code,
                400,
                f"Статус код отличный от 400 при неправильном sheet_name"
            )

    def test_submit_task_wrong_date_name(self):
        """/predict название колонки с датой"""
        with open(BEEF_PRICES_PATH, "rb") as f:
            data = {
                'sheet_name': 'beef',
                'date_name': 'wrong_date',
                'series_name': 'prod',
                'forecasting_steps': 10,
                'year_limit': 10,
                'data_frequency': 'MS',
                'sesoanal_period': 12,
            }
            response = session.post(f"{API_URL}/predict", files={"file": f}, data=data)
            self.assertEqual(
                response.status_code,
                400,
                f"Статус код отличный от 400 при неправильном date_name"
            )

    def test_submit_task_wrong_series_name(self):
        """/predict название колонки с временным рядом"""
        with open(BEEF_PRICES_PATH, "rb") as f:
            data = {
                'sheet_name': 'beef',
                'date_name': 'date',
                'series_name': 'wrong_series_name',
                'forecasting_steps': 10,
                'year_limit': 10,
                'data_frequency': 'MS',
                'sesoanal_period': 12,
            }
            response = session.post(f"{API_URL}/predict", files={"file": f}, data=data)
            self.assertEqual(
                response.status_code,
                400,
                f"Статус код отличный от 400 при неправильном series_name"
            )

    def test_submit_task_dataset_less_tan_three_seasons(self):
        """/predict минимальная длина временного ряда"""
        with open(BEEF_PRICES_PATH, "rb") as f:
            data = {
                'sheet_name': 'beef',
                'date_name': 'date',
                'series_name': 'prod',
                'forecasting_steps': 10,
                'year_limit': 1,
                'data_frequency': 'MS',
                'sesoanal_period': 12,
            }
            response = session.post(f"{API_URL}/predict", files={"file": f}, data=data)
            self.assertEqual(
                response.status_code,
                400,
                f"Статус код отличный от 400 при датасете размером меньше, чем 3 сезона"
            )

    def test_submit_task_unknown_frequency(self):
        """/predict неизвестная частота данных"""
        with open(BEEF_PRICES_PATH, "rb") as f:
            data = {
                'sheet_name': 'beef',
                'date_name': 'date',
                'series_name': 'prod',
                'forecasting_steps': 10,
                'year_limit': 10,
                'data_frequency': 'some_invalid_frequency',
                'sesoanal_period': 12,
            }
            response = session.post(f"{API_URL}/predict", files={"file": f}, data=data)
            self.assertEqual(
                response.status_code,
                422,
                f"Статус код отличный от 400 при неизвестной частоте данных"
            )

    def test_submit_task_extra_long_seasonal_period(self):
        """/predict длина периода не соответствует количеству данных"""
        with open(BEEF_PRICES_PATH, "rb") as f:
            data = {
                'sheet_name': 'beef',
                'date_name': 'date',
                'series_name': 'prod',
                'forecasting_steps': 10,
                'year_limit': 10,
                'data_frequency': 'MS',
                'sesoanal_period': 365,
            }
            response = session.post(f"{API_URL}/predict", files={"file": f}, data=data)
            self.assertEqual(
                response.status_code,
                400,
                f"Статус код отличный от 400 при несоответствии длины сезона с данными"
            )

    def test_submit_task_authorization(self):
        """/predict отсутствие авторизации"""
        response = requests.post(f"{API_URL}/predict", files={}, data={})
        self.assertEqual(
            response.status_code,
            401,
            f"Статус код отличный от 401 при отсутствии заголовка авторизции"
        )

    def test_status_authorization(self):
        """/status/{task_id} отсутствие авторизации"""
        response = requests.get(f"{API_URL}/status/1")
        self.assertEqual(
            response.status_code,
            401,
            f"Статус код отличный от 401 при отсутствии заголовка авторизции"
        )

    def test_get_forecasting_result_authorization(self):
        """/result/{task_id} отсутствие авторизации"""
        response = requests.get(f"{API_URL}/result/1")
        self.assertEqual(
            response.status_code,
            401,
            f"Статус код отличный от 401 при отсутствии заголовка авторизции"
        )

    def test_submit_task_wrong_authorization_credentials(self):
        """/predict неправильные логин и пароль"""
        response = requests.post(f"{API_URL}/predict", files={}, data={}, auth=('test', 'test'))
        self.assertEqual(
            response.status_code,
            401,
            f"Статус код отличный от 401 при неправильном логине или пароле"
        )


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(TestApiEndpoints())
    test_suite.addTest(TestApiValidation())

    return test_suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
