import requests


def test_request_models_200(api_config):
    """Тест эндпоинта запроса моделей"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json'
    })

    response = requests.get(f"{base_url}/v1/models", headers=headers)
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'data' in response_data


def test_request_models_without_auth_403(api_config):
    """Тест эндпоинта запроса моделей без аутентификации"""
    base_url = api_config["base_url"]
    headers = {
        'accept': 'application/json'
    }

    response = requests.get(f"{base_url}/v1/models", headers=headers)
    assert response.status_code == 403  # Forbidden
