#!/usr/bin/env python3
"""Простой тест функционала extract_document."""

import asyncio
import sys
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent))

from src.document_extractor import get_document_extractor


async def test_pdf_extraction():
    """Тест извлечения из PDF."""
    print("=" * 80)
    print("Тест: Извлечение из PDF (IFA.pdf)")
    print("=" * 80)

    extractor = get_document_extractor()
    result = await extractor.extract_text("test_documents/IFA.pdf")

    if result["success"]:
        print("✅ Успешно!")
        print(f"\nМетаданные:")
        for key, value in result["metadata"].items():
            if key not in ["saved_pages", "saved_images"]:
                print(f"  {key}: {value}")

        if result["metadata"].get("saved_pages"):
            print(f"\n Сохранено страниц: {len(result['metadata']['saved_pages'])}")
            print("  Первые 3 файла:")
            for page in result["metadata"]["saved_pages"][:3]:
                print(f"    - {page}")

        if result["metadata"].get("saved_images"):
            print(f"\n✨ Извлечено изображений: {len(result['metadata']['saved_images'])}")
            for img in result["metadata"]["saved_images"]:
                print(f"    - {img}")

        print(f"\n📝 Текст (первые 200 символов):")
        print(result["text"][:200])
        print("...")
    else:
        print(f"❌ Ошибка: {result['error']}")

    print("\n")


async def test_docx_extraction():
    """Тест извлечения из DOCX."""
    print("=" * 80)
    print("Тест: Извлечение из DOCX (test_document.docx)")
    print("=" * 80)

    extractor = get_document_extractor()
    result = await extractor.extract_text("test_documents/test_document.docx")

    if result["success"]:
        print("✅ Успешно!")
        print(f"\nМетаданные:")
        for key, value in result["metadata"].items():
            if key not in ["saved_pages", "saved_images"]:
                print(f"  {key}: {value}")

        if result["metadata"].get("saved_pages"):
            print(f"\n📄 Сохранено файлов: {len(result['metadata']['saved_pages'])}")
            for page in result["metadata"]["saved_pages"]:
                print(f"    - {page}")

        print(f"\n📝 Текст (первые 200 символов):")
        print(result["text"][:200])
        print("...")
    else:
        print(f"❌ Ошибка: {result['error']}")

    print("\n")


async def main():
    """Запуск всех тестов."""
    print("\n🧪 Тестирование модуля document_extractor\n")

    # Тест PDF с OCR и изображениями
    await test_pdf_extraction()

    # Задержка между запросами (rate limit)
    print("⏳ Ожидание 3 секунды (rate limit)...\n")
    await asyncio.sleep(3)

    # Тест DOCX
    await test_docx_extraction()

    print("✅ Все тесты завершены!")
    print(f"\n📁 Проверьте директорию 'extracted_documents/' для результатов")


if __name__ == "__main__":
    asyncio.run(main())
