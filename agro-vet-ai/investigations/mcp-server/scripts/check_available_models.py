#!/usr/bin/env python3
"""Проверка доступных моделей эмбеддингов через VseGPT API."""

import asyncio
import sys
from pathlib import Path

# Добавляем родительскую папку в путь поиска модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.embeddings import get_embeddings_generator
from src.config import settings


async def main():
    print("=== Проверка моделей эмбеддингов ===\n")

    print(f"Текущая конфигурация:")
    print(f"  API Base: {settings.openai_api_base}")
    print(f"  Модель: {settings.embedding_model}")
    print(f"  Размерность: {settings.embedding_dimension}")
    print()

    emb_gen = get_embeddings_generator()

    # Тестовая фраза
    test_text = "антибактериальная терапия"

    # Тестируем разные модели
    models_to_test = [
        ("text-embedding-ada-002", 1536),
        ("text-embedding-3-small", 1536),
        ("text-embedding-3-large", 3072),
        ("text-embedding-3-large", 1536),  # С уменьшенной размерностью
    ]

    for model, dimension in models_to_test:
        print(f"Тест модели: {model} (dimension={dimension})")

        try:
            # Временно меняем модель
            original_model = emb_gen.model
            original_dimension = emb_gen.dimension

            emb_gen.model = model
            emb_gen.dimension = dimension

            # Пытаемся создать эмбеддинг с указанием размерности
            response = await emb_gen.client.embeddings.create(
                model=model,
                input=test_text,
                encoding_format="float",
                dimensions=dimension,  # Явно указываем размерность
            )

            embedding = response.data[0].embedding

            print(f"  ✅ Успешно: dimension={len(embedding)}")
            print(f"  Первые 5 значений: {embedding[:5]}")

            # Восстанавливаем оригинальные настройки
            emb_gen.model = original_model
            emb_gen.dimension = original_dimension

        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            # Восстанавливаем оригинальные настройки
            emb_gen.model = original_model
            emb_gen.dimension = original_dimension

        print()

    await emb_gen.close()


if __name__ == "__main__":
    asyncio.run(main())
