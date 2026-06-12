import pytest
import requests
import json
from pathlib import Path


def test_basic_submit_request_200(api_config):
    """Тест базового запроса отправки"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    files = {
        "message": (None, "Какие симптомы у классической чумы свиней?")
    }
    response = requests.post(f"{base_url}/api/submit", files=files, headers=headers)
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'response' in response_data


def test_submit_without_message_and_file_400(api_config):
    """Тест запроса отправки без сообщения и файла (должен вернуть ошибку)"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    files = {}
    response = requests.post(f"{base_url}/api/submit", files=files, headers=headers)
    assert response.status_code == 400  # Bad Request


def test_submit_without_auth_403(api_config):
    """Тест запроса отправки без аутентификации"""
    base_url = api_config["base_url"]

    files = {
        "message": (None, "Какие симптомы у классической чумы свиней?")
    }
    response = requests.post(f"{base_url}/api/submit", files=files)
    assert response.status_code == 403  # Forbidden


def test_submit_with_invalid_json_dialog_history_422(api_config):
    """Тест запроса отправки с недействительным JSON в истории диалога"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    files = {
        "message": (None, "Тест"),
        "dialog_history": (None, "invalid json")
    }
    response = requests.post(f"{base_url}/api/submit", files=files, headers=headers)
    assert response.status_code == 422


def test_pcr_file_upload_200(api_config):
    """Тест загрузки файла ПЦР-теста"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    # Check if test file exists
    pcr_file_path = Path("tests/1724_ГК_ВИК__пцр.pdf")
    if not pcr_file_path.exists():
        pytest.skip(f"Тестовый файл {pcr_file_path} не найден")

    with open(pcr_file_path, "rb") as pcr_file:
        files = {
            "message": (None, "Проанализируй пцр тест"),
            "file_contents": ("1724_ГК_ВИК__пцр.pdf", pcr_file, "application/pdf")
        }
        response = requests.post(f"{base_url}/api/submit", files=files, headers=headers)
        assert response.status_code == 200
        assert response.headers.get('content-type', '').startswith('application/json')
        response_data = response.json()
        assert isinstance(response_data, dict)
        assert 'response' in response_data


def test_ifa_file_upload_200(api_config):
    """Тест загрузки файла ИФА-теста"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    # Check if test file exists
    ifa_file_path = Path("tests/IFA.pdf")
    if not ifa_file_path.exists():
        pytest.skip(f"Тестовый файл {ifa_file_path} не найден")

    with open(ifa_file_path, "rb") as ifa_file:
        files = {
            "message": (None, "Проанализируй ифа тест"),
            "file_contents": ("IFA.pdf", ifa_file, "application/pdf")
        }
        response = requests.post(f"{base_url}/api/submit", files=files, headers=headers)
        assert response.status_code == 200
        assert response.headers.get('content-type', '').startswith('application/json')
        response_data = response.json()
        assert isinstance(response_data, dict)
        assert 'response' in response_data


def test_request_with_dialog_history_multipart_200(api_config):
    """Тест запроса с историей диалога с использованием multipart/form-data"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    dialog_history = {
        "dialog": [
            {"role": "user", "content": "Привет"},
            {"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"}
        ]
    }

    files = {
        "message": (None, "Какие симптомы у птичьего гриппа?"),
        "dialog_history": (None, json.dumps(dialog_history))
    }
    response = requests.post(f"{base_url}/api/submit", files=files, headers=headers)
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'response' in response_data
