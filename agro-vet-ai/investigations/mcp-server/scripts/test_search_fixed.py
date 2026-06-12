#!/usr/bin/env python3
"""Тест векторного поиска с правильной моделью."""

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
    print("=== Тест векторного поиска с правильной моделью ===\n")

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base,
    )

    kb = await get_knowledge_base()

    queries = [
        "antimicrobial therapy",
        "antibiotic treatment for pigs",
        "E. coli infection",
        "антибиотики для свиней",
    ]

    try:
        for query in queries:
            print(f"Запрос: '{query}'")

            # Генерируем эмбеддинг с правильной моделью
            response = await client.embeddings.create(
                model=settings.embedding_model,
                input=query,
                encoding_format="float",
            )

            embedding = response.data[0].embedding
            print(f"  Модель: {settings.embedding_model}")
            print(f"  Размерность: {len(embedding)}")

            # Прямой поиск в БД
            embedding_str = "[" + ", ".join(f"{x:.10f}" for x in embedding) + "]"

            sql = f"""
                SELECT
                    content,
                    source_document,
                    page_number,
                    embedding <=> '{embedding_str}' as distance
                FROM knowledge_base_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> '{embedding_str}' ASC
                LIMIT 5
            """

            async with kb.pool.acquire() as conn:
                rows = await conn.fetch(sql)

            print(f"  Топ-5 результатов:")
            for i, row in enumerate(rows, 1):
                distance = row["distance"]
                content = row["content"][:80].replace('\n', ' ')
                print(f"    [{i}] Distance: {distance:.6f}")
                print(f"        {content}...")

            print()

    finally:
        await client.close()
        await kb.close()


if __name__ == "__main__":
    asyncio.run(main())
