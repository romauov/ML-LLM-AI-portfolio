import time
import requests
import logger as _logger
from metrics import TIMEOUT


def submit(api_config, message: str) -> dict:
    base_url = api_config["base_url"]
    headers = api_config["headers"].copy()
    headers.update({"accept": "application/json", "Content-Type": "application/json"})
    body = {"messages": [{"role": "user", "content": message}]}
    model = api_config.get("model")
    if model:
        body["model"] = model
    t0 = time.monotonic()
    text = None
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=body,
            headers=headers,
            timeout=TIMEOUT,
        )
        assert response.status_code == 200, f"Статус {response.status_code}: {response.text}"
        data = response.json()
        assert "choices" in data and data["choices"], f"Нет поля 'choices' в ответе: {data}"
        text = data["choices"][0]["message"]["content"]
        return {"response": text, "query": message, "elapsed": time.monotonic() - t0}
    finally:
        _logger.update(
            query=message,
            agent_response=text,
            query_processing_duration=round(time.monotonic() - t0, 1),
        )
