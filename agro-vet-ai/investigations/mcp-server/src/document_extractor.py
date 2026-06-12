"""Модуль для извлечения текста из документов (PDF, DOCX) через VseGPT API.

Предоставляет функциональность для извлечения текста из лабораторных результатов,
договоров и других документов с использованием моделей extract-text и pdf-ocr.
"""

import asyncio
import base64
from pathlib import Path
from typing import Dict, Any
from unicodedata import normalize

import requests

from .config import settings

import logging

logger = logging.getLogger(__name__)

# Поддерживаемые форматы документов
SUPPORTED_FORMATS = {".pdf", ".docx"}

# Маппинг моделей
MODEL_MAP = {
    "auto": None,  # Автоматический выбор
    "extract-text": "utils/extract-text-1.0",
    "pdf-ocr": "utils/pdf-ocr-1.0"
}


class DocumentExtractor:
    """Экстрактор текста из документов с использованием VseGPT API."""

    def __init__(self):
        """Инициализация экстрактора с API ключом."""
        self.api_key = settings.openai_api_key
        self.api_url = "https://api.vsegpt.ru/v1/extract_text"
        self.max_retries = 3
        self.retry_delay = 1.5  # секунды

    def _sanitize_filename(self, filename: str) -> str:
        """Очистка имени файла от кириллицы и спецсимволов.

        Args:
            filename: Оригинальное имя файла

        Returns:
            Безопасное имя файла в латинице
        """
        # Нормализация Unicode
        filename = normalize('NFKD', filename)

        # Простая транслитерация кириллицы
        cyrillic_to_latin = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
            'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
            'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
            'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
            'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '',
            'э': 'e', 'ю': 'yu', 'я': 'ya'
        }

        result = []
        for char in filename.lower():
            if char in cyrillic_to_latin:
                result.append(cyrillic_to_latin[char])
            elif char.isascii() and (char.isalnum() or char in '.-_ '):
                result.append(char)
            else:
                result.append('_')

        return ''.join(result)

    def _select_model(self, file_path: Path, user_choice: str) -> str:
        """Выбор модели для извлечения текста.

        Args:
            file_path: Путь к файлу
            user_choice: Выбор пользователя ('auto', 'extract-text', 'pdf-ocr')

        Returns:
            Название модели API

        Raises:
            ValueError: Если формат файла не поддерживается
        """
        ext = file_path.suffix.lower()

        if ext not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Формат {ext} не поддерживается. "
                f"Поддерживаемые форматы: {', '.join(SUPPORTED_FORMATS)}"
            )

        # Если пользователь явно указал модель
        if user_choice != "auto":
            model = MODEL_MAP[user_choice]
            # Проверка совместимости
            if user_choice == "pdf-ocr" and ext != ".pdf":
                raise ValueError(
                    f"Модель pdf-ocr поддерживает только PDF файлы, "
                    f"получен формат {ext}"
                )
            return model

        # Автоматический выбор
        if ext == ".pdf":
            return "utils/pdf-ocr-1.0"  # OCR для лучшего качества таблиц
        elif ext == ".docx":
            return "utils/extract-text-1.0"

        raise ValueError(f"Неподдерживаемый формат: {ext}")

    async def extract_text(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """Извлечение текста из документа с сохранением в файлы.

        Автоматически выбирает модель, извлекает изображения из PDF,
        сохраняет каждую страницу в отдельный MD файл.

        Args:
            file_path: Абсолютный путь к файлу

        Returns:
            Словарь с результатом:
            {
                "success": bool,
                "text": str (если success=True),
                "error": str (если success=False),
                "metadata": {
                    "filename": str,
                    "output_dir": str,
                    "saved_pages": List[str],
                    "saved_images": List[str],
                    ...
                }
            }

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если формат файла не поддерживается
        """
        file_path = Path(file_path).resolve()

        # Проверка существования файла
        if not file_path.exists():
            return {
                "success": False,
                "error": f"Файл не найден: {file_path}",
                "metadata": {"filename": file_path.name, "error_code": "FILE_NOT_FOUND"}
            }

        try:
            # Выбор модели (автоматически)
            selected_model = self._select_model(file_path, "auto")

            # Чтение и кодирование файла
            with open(file_path, "rb") as f:
                file_content = f.read()

            encoded_file = base64.b64encode(file_content).decode('utf-8')

            # Безопасное имя файла
            safe_filename = self._sanitize_filename(file_path.name)

            # Подготовка запроса
            payload = {
                "encoded_base64_file": encoded_file,
                "filename": safe_filename,
                "model": selected_model,
            }

            # Для OCR модели - всегда извлекаем изображения
            if selected_model == "utils/pdf-ocr-1.0":
                payload["return_images"] = True

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-Title": f"VetRetro document extraction: {safe_filename}"
            }

            # Отправка запроса с retry логикой
            result = await self._call_api_with_retry(headers, payload)

            # DEBUG: Сохранение полного ответа API
            import json
            debug_file = Path("api_response_debug.json")
            with open(debug_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"API response saved to {debug_file}")

            # Создание директории для сохранения
            output_dir = await self._create_output_directory(file_path)

            # Сохранение страниц и изображений
            saved_pages, saved_images = await self._save_extraction_results(
                result, output_dir
            )

            # Форматирование ответа
            metadata = {
                "filename": file_path.name,
                "file_size_bytes": len(file_content),
                "model_used": selected_model,
                "output_dir": str(output_dir),
                "saved_pages": saved_pages,
                "saved_images": saved_images,
            }

            # Извлечение метаданных из ответа
            if "pages" in result:
                metadata["pages_processed"] = len(result["pages"])
                metadata["has_images"] = any(
                    page.get("images") for page in result["pages"]
                )
                if metadata["has_images"]:
                    metadata["images_count"] = sum(
                        len(page.get("images", []))
                        for page in result["pages"]
                    )

            if "usage_info" in result:
                metadata.update(result["usage_info"])

            return {
                "success": True,
                "text": result.get("text", ""),
                "metadata": metadata
            }

        except ValueError as e:
            # Неподдерживаемый формат
            logger.error(f"Ошибка валидации: {e}")
            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "filename": file_path.name,
                    "error_code": "VALIDATION_ERROR"
                }
            }

        except requests.HTTPError as e:
            # HTTP ошибки от API
            logger.error(f"HTTP ошибка при вызове API: {e}")

            error_message = f"Ошибка API: {e.response.status_code}"
            if e.response.status_code == 500:
                error_message = (
                    "Формат файла не поддерживается API или файл поврежден. "
                    f"(HTTP 500)"
                )
            elif e.response.status_code == 429:
                error_message = "Превышен лимит запросов к API. Попробуйте позже."

            return {
                "success": False,
                "error": error_message,
                "metadata": {
                    "filename": file_path.name,
                    "error_code": f"HTTP_{e.response.status_code}"
                }
            }

        except Exception as e:
            # Неожиданные ошибки
            logger.exception(f"Неожиданная ошибка при извлечении текста: {e}")
            return {
                "success": False,
                "error": f"Внутренняя ошибка: {str(e)}",
                "metadata": {
                    "filename": file_path.name,
                    "error_code": "INTERNAL_ERROR"
                }
            }

    async def _create_output_directory(self, file_path: Path) -> Path:
        """Создание директории для сохранения извлеченного контента.

        Args:
            file_path: Путь к исходному файлу

        Returns:
            Path к созданной директории
        """
        # Базовая директория для всех извлечений
        base_dir = Path("extracted_documents")
        base_dir.mkdir(exist_ok=True)

        # Имя директории на основе имени файла
        doc_name = file_path.stem  # Имя без расширения
        safe_doc_name = self._sanitize_filename(doc_name)

        output_dir = base_dir / safe_doc_name

        # Если директория уже существует, добавляем суффикс
        if output_dir.exists():
            counter = 1
            while (base_dir / f"{safe_doc_name}_{counter}").exists():
                counter += 1
            output_dir = base_dir / f"{safe_doc_name}_{counter}"

        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Создана директория для извлечения: {output_dir}")

        return output_dir

    async def _save_extraction_results(
        self,
        api_result: dict,
        output_dir: Path
    ) -> tuple[list[str], list[str]]:
        """Сохранение страниц и изображений в файлы.

        Args:
            api_result: Результат от API
            output_dir: Директория для сохранения

        Returns:
            Кортеж (список файлов страниц, список файлов изображений)
        """
        saved_pages = []
        saved_images = []

        # Если есть информация о страницах (OCR модель)
        if "pages" in api_result:
            for page in api_result["pages"]:
                page_index = page.get("index", 0)
                page_num = page_index + 1

                # Сохранение markdown страницы
                page_file = output_dir / f"page_{page_num:03d}.md"
                page_content = page.get("markdown", "")

                with open(page_file, "w", encoding="utf-8") as f:
                    f.write(f"# Страница {page_num}\n\n")
                    f.write(page_content)

                saved_pages.append(str(page_file.relative_to("extracted_documents")))

                # Сохранение изображений со страницы
                if "images" in page and page["images"]:
                    for img in page["images"]:
                        img_id = img.get("id", f"img-{len(saved_images)}")
                        img_base64 = img.get("image_base64")

                        logger.debug(f"Image {img_id}: base64={'present' if img_base64 else 'null/empty'}, length={len(img_base64) if img_base64 else 0}")

                        if img_base64:
                            # Декодирование и сохранение изображения
                            img_data = base64.b64decode(img_base64)
                            img_file = output_dir / img_id

                            with open(img_file, "wb") as f:
                                f.write(img_data)

                            saved_images.append(
                                str(img_file.relative_to("extracted_documents"))
                            )
                            logger.info(f"Сохранено изображение: {img_file} ({len(img_data)} bytes)")
                        else:
                            logger.warning(f"Пропущено изображение {img_id}: base64 отсутствует")
        else:
            # Для не-OCR модели (docx) - сохраняем весь текст в один файл
            text = api_result.get("text", "")
            if text:
                page_file = output_dir / "content.md"
                with open(page_file, "w", encoding="utf-8") as f:
                    f.write(text)
                saved_pages.append(str(page_file.relative_to("extracted_documents")))

        logger.info(
            f"Сохранено: {len(saved_pages)} страниц, "
            f"{len(saved_images)} изображений в {output_dir}"
        )

        return saved_pages, saved_images

    async def _call_api_with_retry(
        self,
        headers: dict,
        payload: dict
    ) -> dict:
        """Вызов API с автоматическими повторами при ошибках.

        Args:
            headers: HTTP заголовки
            payload: Данные запроса

        Returns:
            Ответ API

        Raises:
            requests.HTTPError: При неудачных запросах после всех повторов
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Отправка запроса к API (попытка {attempt + 1}/{self.max_retries})")

                # Выполняем синхронный запрос в отдельном потоке
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.post(
                        self.api_url,
                        headers=headers,
                        json=payload,
                        timeout=120
                    )
                )

                response.raise_for_status()
                return response.json()

            except requests.HTTPError as e:
                last_error = e

                # Для 500 ошибок (rate limit или unsupported format)
                # делаем retry с задержкой
                if e.response.status_code == 500 and attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Получена ошибка 500, повтор через {delay:.1f}с "
                        f"(попытка {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue

                # Для остальных HTTP ошибок - сразу пробрасываем
                raise

            except Exception as e:
                logger.error(f"Непредвиденная ошибка при запросе к API: {e}")
                raise

        # Если все попытки исчерпаны
        if last_error:
            raise last_error

        raise RuntimeError("Не удалось выполнить запрос к API")


# Глобальный экземпляр экстрактора
_document_extractor: DocumentExtractor | None = None


def get_document_extractor() -> DocumentExtractor:
    """Получить или создать глобальный экземпляр экстрактора документов.

    Returns:
        DocumentExtractor: Глобальный экземпляр экстрактора
    """
    global _document_extractor
    if _document_extractor is None:
        _document_extractor = DocumentExtractor()
    return _document_extractor
