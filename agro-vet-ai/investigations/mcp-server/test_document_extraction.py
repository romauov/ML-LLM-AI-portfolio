#!/usr/bin/env python3
"""Тестовый скрипт для исследования VseGPT API извлечения текста из документов.

Поддерживаемые форматы:
- PDF (utils/extract-text-1.0)
- DOCX (utils/extract-text-1.0)
- PDF с OCR (utils/pdf-ocr-1.0)
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Удаление прокси для корректной работы API
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ftp_proxy', None)
os.environ.pop('all_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)


def extract_text(file_path: str, model: str = "utils/extract-text-1.0",
                 return_images: bool = False) -> dict:
    """Извлечение текста из документа через VseGPT API.

    Args:
        file_path: Путь к файлу
        model: Модель для извлечения ('utils/extract-text-1.0' или 'utils/pdf-ocr-1.0')
        return_images: Возвращать ли картинки в base64 (только для pdf-ocr-1.0)

    Returns:
        dict: Ответ API с извлеченным текстом и метаданными
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY не найден в переменных окружения")

    # Проверка существования файла
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    # Кодирование файла в base64
    with open(file_path, "rb") as file:
        encoded_file = base64.b64encode(file.read()).decode('utf-8')

    # Подготовка запроса
    payload = {
        "encoded_base64_file": encoded_file,
        "filename": file_path.name,
        "model": model,
    }

    if return_images and model == "utils/pdf-ocr-1.0":
        payload["return_images"] = True

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Title": f"Doc2Text test: {file_path.name}"
    }

    # Отправка запроса
    print(f"Отправка запроса для файла: {file_path.name}")
    print(f"Модель: {model}")
    print(f"Размер файла: {file_path.stat().st_size / 1024:.2f} KB")
    print("-" * 80)

    response = requests.post(
        "https://api.vsegpt.ru/v1/extract_text",
        headers=headers,
        json=payload,
        timeout=60
    )

    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(
        description="Тестирование VseGPT API для извлечения текста из документов"
    )
    parser.add_argument("file", help="Путь к файлу (PDF, DOCX, XLSX)")
    parser.add_argument(
        "--model",
        choices=["extract-text", "pdf-ocr"],
        default="extract-text",
        help="Модель для использования (default: extract-text)"
    )
    parser.add_argument(
        "--with-images",
        action="store_true",
        help="Возвращать картинки в base64 (только для pdf-ocr)"
    )
    parser.add_argument(
        "--output",
        help="Сохранить результат в JSON файл"
    )

    args = parser.parse_args()

    # Определение модели
    model_map = {
        "extract-text": "utils/extract-text-1.0",
        "pdf-ocr": "utils/pdf-ocr-1.0"
    }
    model = model_map[args.model]

    try:
        result = extract_text(
            args.file,
            model=model,
            return_images=args.with_images
        )

        # Вывод результатов
        print("\n" + "=" * 80)
        print("РЕЗУЛЬТАТ ИЗВЛЕЧЕНИЯ ТЕКСТА")
        print("=" * 80 + "\n")

        if "text" in result:
            print("ИЗВЛЕЧЕННЫЙ ТЕКСТ:")
            print("-" * 80)
            print(result["text"])
            print("-" * 80)

        # Дополнительная информация
        print("\nМЕТАДАННЫЕ:")
        for key, value in result.items():
            if key != "text" and key != "images":
                print(f"  {key}: {value}")

        if "images" in result:
            print(f"\n  Количество картинок: {len(result['images'])}")

        # Сохранение в файл если указано
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nРезультат сохранен в: {args.output}")

        return 0

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
