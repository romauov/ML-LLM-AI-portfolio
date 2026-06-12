import pytest
import requests
from pathlib import Path


def test_process_lab_results_with_text_200(api_config):
    """Тест обработки лабораторных результатов с текстовыми данными"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    files = {
        "message": (None, "Анализ лабораторных результатов"),
        "lab_results": (None, "Результаты анализов: уровень глюкозы 5.5 ммоль/л")
    }
    response = requests.post(f"{base_url}/api/process_lab_results", files=files, headers=headers)
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'response' in response_data


def test_process_lab_results_with_ifa_file_200(api_config):
    """Тест обработки лабораторных результатов с загрузкой файла ИФА"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    # Проверить, существует ли тестовый файл
    test_file_path = Path("tests/IFA.pdf")
    if not test_file_path.exists():
        pytest.skip(f"Тестовый файл {test_file_path} не найден")

    with open(test_file_path, "rb") as test_file:
        files = {
            "message": (None, "Анализ лабораторных результатов"),
            "file_contents": ("IFA.pdf", test_file, "application/pdf")
        }
        response = requests.post(f"{base_url}/api/process_lab_results", files=files, headers=headers)
        assert response.status_code == 200
        assert response.headers.get('content-type', '').startswith('application/json')
        response_data = response.json()
        assert isinstance(response_data, dict)
        assert 'response' in response_data


def test_process_lab_results_with_pcr_file_200(api_config):
    """Тест обработки лабораторных результатов с загрузкой файла ПЦР"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    # Проверить, существует ли тестовый файл
    test_file_path = Path("tests/1724_ГК_ВИК__пцр.pdf")
    if not test_file_path.exists():
        pytest.skip(f"Тестовый файл {test_file_path} не найден")

    with open(test_file_path, "rb") as test_file:
        files = {
            "message": (None, "Анализ лабораторных результатов"),
            "file_contents": ("1724_ГК_ВИК__пцр.pdf", test_file, "application/pdf")
        }
        response = requests.post(f"{base_url}/api/process_lab_results", files=files, headers=headers)
        assert response.status_code == 200
        assert response.headers.get('content-type', '').startswith('application/json')
        response_data = response.json()
        assert isinstance(response_data, dict)
        assert 'response' in response_data


def test_process_lab_results_without_data_400(api_config):
    """Тест обработки лабораторных результатов без текста или файла"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    files = {
        "message": (None, "Анализ лабораторных результатов")
    }
    response = requests.post(f"{base_url}/api/process_lab_results", files=files, headers=headers)
    assert response.status_code == 400  # Bad Request


def test_process_lab_results_with_both_text_and_file_400(api_config):
    """Тест обработки лабораторных результатов с текстом и файлом одновременно"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    # Проверить, существует ли тестовый файл
    test_file_path = Path("tests/IFA.pdf")
    if not test_file_path.exists():
        pytest.skip(f"Тестовый файл {test_file_path} не найден")

    with open(test_file_path, "rb") as test_file:
        files = {
            "message": (None, "Анализ лабораторных результатов"),
            "lab_results": (None, "Результаты анализов: уровень глюкозы 5.5 ммоль/л"),
            "file_contents": ("IFA.pdf", test_file, "application/pdf")
        }
        response = requests.post(f"{base_url}/api/process_lab_results", files=files, headers=headers)
        assert response.status_code == 400  # Bad Request


def test_process_lab_results_without_auth_403(api_config):
    """Тест обработки лабораторных результатов без аутентификации"""
    base_url = api_config["base_url"]

    files = {
        "message": (None, "Анализ лабораторных результатов"),
        "lab_results": (None, "Результаты анализов: уровень глюкозы 5.5 ммоль/л")
    }
    response = requests.post(f"{base_url}/api/process_lab_results", files=files)
    assert response.status_code == 403  # Forbidden
