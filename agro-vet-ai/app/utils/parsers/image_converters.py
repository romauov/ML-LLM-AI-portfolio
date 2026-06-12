import base64
import logging
import os
import pdfplumber
import requests
from PIL import Image
from pdf2image import convert_from_path
from typing import Optional

from config.config import Config
from app.llm.prompts import SYSTEM_PROMPT_BASE
from app.llm.providers.llm_provider import LLMProvider
from app.utils.parsers.base_converter import BaseConverter
from app.utils.settings import secrets as s


class PdfConverter(BaseConverter):
    """Документ PDF, преобразованный в один из других форматов (plain text, Markdown, изображение)."""

    def convert(self) -> Optional[str]:
        """
        Конвертирует PDF-файл в текст.

        :return: Извлечённый текст или None.
        """
        # Извлекаем текст из загруженного файла
        pdf_data = self.convert_with_plumber(self.file_path)

        if not pdf_data:
            logging.warning(
                f"Загруженный PDF-файл {self.file_path} не может быть прочитан. Извлечение текста с помощью LLM.")

            pdf_data = self.convert_with_llm("utils/pdf-ocr-1.0")
            if not pdf_data:
                logging.warning(f"Текст из загруженного PDF-файл {self.file_path} с помощью LLM извлечь не удалось.")

        return pdf_data

    def convert_with_plumber(self, pdf_path) -> str:
        """
        Извлекает текст из PDF-файла с использованием библиотеки pdfplumber.

        :param pdf_path: Путь к PDF-файлу.
        :return: Извлечённый текст.
        """
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                return page.extract_text()

    def convert_with_llm(self, model) -> Optional[str]:
        """
        Извлекает текст из бинарного файла в формате Markdown.

        :param model: Имя модели (например, utils/extract-text-1.0 или utils/pdf-ocr-1.0 для оптического распознавания OCR).
        :return: Ответ от LLM с текстом из PDF-файла в формате Markdown в случае успеха, None в случае ошибки.
        """
        # Получение ключей API из .env

        if not model:
            model = Config.from_yaml().llm_models.ocr_model

        try:
            # Кодируем файл в base64
            with open(self.file_path, "rb") as file:
                encoded_file = base64.b64encode(file.read()).decode('utf-8')

            # Отправляем запрос
            response = requests.post(
                "https://api.vsegpt.ru/v1/extract_text",
                headers={
                    "Authorization": f"Bearer {s.vsegpt_api_key}",
                    "X-Title": "inline-ltd.ru-agro-bot"
                },
                json={
                    "encoded_base64_file": encoded_file,
                    "filename": os.path.basename(self.file_path),
                    "model": model,
                    # "return_images": True, # для utils/pdf-ocr-1.0 также возвращает картинки в base64
                }
            )

            response.raise_for_status()

            # Получаем результат
            return response.json()["text"]

        except Exception as e:
            # Обрабатываем ошибки
            logging.error(f"Произошла ошибка при выполнении запроса: {e}")
            return None

    def convert_to_image(self, pdf_path, image_format="jpeg", merge_into_one=True):
        """
        Преобразует PDF-файл в изображения, опционально объединяя их в одно.

        :param pdf_path: Путь к PDF-файлу.
        :param image_format: Формат сохраняемого изображения (например, 'png', 'jpeg').
        :param merge_into_one: Если True — объединяет все страницы в одно изображение.
        :return: Список путей к изображениям или едиственный путь, если изображения нужно объединить.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Файл не найден: {pdf_path}")

        base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.dirname(pdf_path)

        images = convert_from_path(pdf_path, dpi=200)

        if merge_into_one:
            # Получаем размеры всех изображений
            widths, heights = zip(*(img.size for img in images))

            # Ширина — максимальная, высота — сумма всех высот
            total_width = max(widths)
            total_height = sum(heights)

            # Создаём новое пустое изображение нужного размера
            merged_image = Image.new("RGB", (total_width, total_height), color=(255, 255, 255))

            y_offset = 0
            for img in images:
                merged_image.paste(img, (0, y_offset))
                y_offset += img.height

            output_path = os.path.join(output_dir, f"{base_filename}_merged.{image_format.lower()}")
            merged_image.save(output_path, image_format)
            return output_path
        else:
            image_paths = []
            for i, image in enumerate(images):
                image_filename = f"{base_filename}_page_{i + 1}.{image_format.lower()}"
                image_path = os.path.join(output_dir, image_filename)
                image.save(image_path, image_format)
                image_paths.append(image_path)

            return image_paths


class ImageConverter(BaseConverter):
    """Конвертер изображений. Извлекает текст с изображения с использованием LLM."""

    def convert(self) -> Optional[str]:
        """
        Извлекает текст или описание изображения с помощью модели LLM.

        :return: Текстовое описание изображения в случае успеха, None в случае ошибки..
        """
        try:
            prompt = "О чем говорится в данном изображении?"

            logging.info(f"Промпт запроса\n" + prompt)

            model = "vis-google/gemini-flash-1.5"

            response_format = {"type": "text"}

            # Кодирование файла в в формат base64
            base64_image = None
            with open(self.file_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            logging.info(f"Файл изображения {self.file_path} закодирован в формат base64.")

            params = {
                "temperature": 0.7,
                "extra_headers": {"X-Title": "inline-ltd.ru-agro-bot"},
                "response_format": response_format,
                "dialog_history": "",
                "base64_image": base64_image,
            }

            # Запрос к GPT через новый LLMProvider
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_BASE},
                {"role": "user", "content": prompt},
            ]
            return LLMProvider().ask(messages=messages, params=params, model=model).content

        except Exception as e:
            logging.exception(f"Текст из загруженного файла {self.file_path} с помощью LLM извлечь не удалось.")
            return None
