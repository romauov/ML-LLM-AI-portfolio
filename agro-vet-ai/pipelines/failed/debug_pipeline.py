from typing import Optional
import httpx
from utils.settsings import secrets as s


class Pipeline:
    def __init__(self):
        self.name = "PCR Pipeline"
        self.id = "debug_pipeline"
        self.files = []
        self.ocr_url = "http://app:8000/api/process_lab_results"
        self.api_key = s.api_key

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        self.files = body.get('files', [])
        return body

    async def pipe(self, user_message: str, model_id: str, messages: list, body: dict) -> str:
        if self.files:
            file_path = self.files[0]['file']['path']
            file_name = self.files[0]['file']['filename']
            try:
                with open(file_path, 'rb') as f:
                    file_bytes = f.read()

                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        self.ocr_url,
                        headers={"X-Api-Key": self.api_key},
                        files={"file_contents": (file_name, file_bytes, "application/pdf")},
                        data={"message": user_message or ""}
                    )
                    result = response.json()
                    return result.get("response", str(result))

            except Exception as e:
                return f"Ошибка: {e}"

        else:
            # обычное сообщение — пересылаем в основной API
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "http://app:8000/v1/chat/completions",
                    headers={"X-Api-Key": self.api_key},
                    json=body
                )
                return response.json()