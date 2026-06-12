#!/usr/bin/env python3
"""Тест модели text-embedding-3-small."""

import asyncio
import sys
import os
from pathlib import Path

# Удаление прокси
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ftp_proxy', None)
os.environ.pop('all_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)

# Добавляем родительскую папку в путь поиска модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import AsyncOpenAI
from src.config import settings
from src.knowledge_base import get_knowledge_base


async def main():
    print("=== Тест модели text-embedding-3-small ===\n")

    # Создаем клиента
    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base,
    )

    kb = await get_knowledge_base()

    try:
        # Получаем тестовый текст из БД
        sql = """
            SELECT content, embedding
            FROM knowledge_base_chunks
            WHERE embedding IS NOT NULL
            LIMIT 1
        """

        async with kb.pool.acquire() as conn:
            row = await conn.fetchrow(sql)

        test_text = row["content"]
        db_embedding_str = str(row["embedding"])

        print(f"Тестовый текст (первые 100 символов):")
        print(f"{test_text[:100].replace(chr(10), ' ')}...\n")

        # Тестируем разные модели
        models = [
            "text-embedding-ada-002",
            "text-embedding-3-small",
        ]

        for model in models:
            print(f"Модель: {model}")

            try:
                response = await client.embeddings.create(
                    model=model,
                    input=test_text,
                    encoding_format="float",
                )

                embedding = response.data[0].embedding
                print(f"  Размерность: {len(embedding)}")
                print(f"  Первые 5 значений: {embedding[:5]}")

                # Сравниваем с БД
                embedding_str = "[" + ", ".join(f"{x:.10f}" for x in embedding) + "]"

                sql_compare = f"""
                    SELECT embedding <=> '{embedding_str}' as distance
                    FROM knowledge_base_chunks
                    WHERE content = $1
                    LIMIT 1
                """

                async with kb.pool.acquire() as conn:
                    result = await conn.fetchrow(sql_compare, test_text)

                distance = result["distance"]
                print(f"  Distance с БД: {distance:.6f}")

                if distance < 0.01:
                    print(f"  ✅ СОВПАДЕНИЕ! Это правильная модель!")
                elif distance < 0.1:
                    print(f"  ⚠️  Небольшое расхождение")
                else:
                    print(f"  ❌ Не совпадает")

            except Exception as e:
                print(f"  ❌ Ошибка: {e}")

            print()

    finally:
        await client.close()
        await kb.close()


if __name__ == "__main__":
    asyncio.run(main())
