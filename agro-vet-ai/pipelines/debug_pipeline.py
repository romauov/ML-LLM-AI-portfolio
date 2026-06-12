import os
from typing import Optional, Iterator
import httpx


class Pipeline:
    def __init__(self):
        self.name = "PCR Pipeline"
        self.id = "debug_pipeline"
        self.files = []
        self.ocr_url = "http://app:8000/api/process_lab_results"
        self.api_key = os.getenv("API_KEY", "")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        self.files = body.get('files', [])
        return body

    def pipe(self, user_message: str, model_id: str, messages: list, body: dict) -> str:
        if self.files:
            file_path = self.files[0]['file']['path']
            file_name = self.files[0]['file']['filename']
            try:
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()

                with httpx.Client(timeout=60) as client:
                    response = client.post(
                        self.ocr_url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files={"file_contents": (file_name, file_bytes, "application/pdf")},
                        data={"message": user_message or ""}
                    )
                    result = response.json()
                    return result.get("response", str(result))

            except Exception as e:
                return f"Ошибка: {e}"
        else:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    "http://app:8000/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body
                )
                return response.json()