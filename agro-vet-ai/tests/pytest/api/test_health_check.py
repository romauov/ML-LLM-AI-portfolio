import requests


def test_api_health_check_200(api_config):
    """Тест эндпоинта проверки работоспособности API"""
    base_url = api_config["base_url"]
    headers = api_config["headers"]

    response = requests.get(f"{base_url}/api/up", headers=headers)
    assert response.status_code == 200
    assert response.text == '"API up"'


def test_api_health_check_without_auth_403(api_config):
    """Тест эндпоинта проверки работоспособности API без аутентификации"""
    base_url = api_config["base_url"]

    response = requests.get(f"{base_url}/api/up")
    assert response.status_code == 403  # Forbidden
