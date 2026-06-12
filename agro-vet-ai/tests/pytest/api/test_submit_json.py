import requests


def test_submit_json_basic_200(api_config):
    """Тест базового запроса отправки JSON"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json',
        'Content-Type': 'application/json'
    })

    payload = {
        "message": "Какие симптомы у классической чумы свиней?"
    }

    response = requests.post(
        f"{base_url}/api/submit_json", json=payload, headers=headers
    )
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'response' in response_data


def test_submit_json_with_invalid_json_422(api_config):
    """Тест запроса отправки JSON с недействительной структурой JSON"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json',
        'Content-Type': 'application/json'
    })

    invalid_payload_str = '{"message": "test", "invalid_json": }'  # Invalid JSON

    response = requests.post(
        f"{base_url}/api/submit_json",
        data=invalid_payload_str,
        headers=headers
    )
    assert response.status_code == 422


def test_submit_json_with_invalid_fields_200(api_config):
    """Тест запроса отправки JSON с непредусмотренными полями"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json',
        'Content-Type': 'application/json'
    })

    payload = {
        "message": "Тест с непредусмотренными полями",
        "unexpected_field": "value",
        "another_field": 123
    }

    response = requests.post(
        f"{base_url}/api/submit_json", json=payload, headers=headers
    )
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'response' in response_data


def test_submit_json_with_dialog_history_200(api_config):
    """Тест запроса отправки JSON с историей диалога"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json',
        'Content-Type': 'application/json'
    })

    payload = {
        "message": "Какие симптомы у птичьего гриппа?",
        "dialog_history": [
            {"role": "user", "content": "Привет"},
            {"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"}
        ]
    }

    response = requests.post(
        f"{base_url}/api/submit_json", json=payload, headers=headers
    )
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'response' in response_data


def test_submit_json_with_forced_topics_200(api_config):
    """Тест запроса отправки JSON с принудительными темами"""
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({
        'accept': 'application/json',
        'Content-Type': 'application/json'
    })

    payload = {
        "message": "Какие симптомы у птичьего гриппа?",
        "forced_topics": ["avian_disease_diagnosis"]
    }

    response = requests.post(
        f"{base_url}/api/submit_json", json=payload, headers=headers
    )
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/json')
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert 'response' in response_data


def test_submit_json_without_auth_403(api_config):
    """Тест запроса отправки JSON без аутентификации"""
    base_url = api_config["base_url"]
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    payload = {
        "message": "Какие симптомы у классической чумы свиней?"
    }

    response = requests.post(
        f"{base_url}/api/submit_json", json=payload, headers=headers
    )
    assert response.status_code == 403  # Forbidden
