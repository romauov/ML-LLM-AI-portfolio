import requests


def test_request_with_dialog_history_json_200(api_config):
    """Тест запроса с историей диалога с использованием JSON-полезной нагрузки"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json',
        'Content-Type': 'application/json'
    })

    payload = {
        "model": "INLINE Vet-bot",
        "messages": [
            {"role": "user", "content": "Привет"},
            {"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"},
            {"role": "user", "content": "Какие симптомы у птичьего гриппа?"}
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }

    response = requests.post(
        f"{base_url}/v1/chat/completions", json=payload, headers=headers
    )
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'id' in response_data
    assert 'choices' in response_data
    assert 'usage' in response_data


def test_request_without_auth_403(api_config):
    """Тест запроса с историей диалога без аутентификации"""
    base_url = api_config["base_url"]
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    payload = {
        "model": "INLINE Vet-bot",
        "messages": [
            {"role": "user", "content": "Привет"},
            {"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"},
            {"role": "user", "content": "Какие симптомы у птичьего гриппа?"}
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }

    response = requests.post(
        f"{base_url}/v1/chat/completions", json=payload, headers=headers
    )
    assert response.status_code == 403  # Forbidden


def test_request_with_invalid_json_422(api_config):
    """Тест запроса с недействительным JSON"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json',
        'Content-Type': 'application/json'
    })

    # Invalid payload - missing required fields
    payload = {
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }

    response = requests.post(
        f"{base_url}/v1/chat/completions", json=payload, headers=headers
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_request_with_invalid_message_structure_422(api_config):
    """Тест запроса с недействительной структурой сообщения"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json',
        'Content-Type': 'application/json'
    })

    payload = {
        "model": "INLINE Vet-bot",
        "messages": [
            {"role": "user"}  # Missing content field
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }

    response = requests.post(
        f"{base_url}/v1/chat/completions", json=payload, headers=headers
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_request_with_invalid_model_200(api_config):
    """Тест запроса с недействительным именем модели"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json',
        'Content-Type': 'application/json'
    })

    payload = {
        "model": "non-existent-model",
        "messages": [
            {"role": "user", "content": "Тест"}
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }

    response = requests.post(
        f"{base_url}/v1/chat/completions", json=payload, headers=headers
    )
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'id' in response_data
    assert 'choices' in response_data
    assert 'usage' in response_data
