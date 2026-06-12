"""Проверка эмбеддингов в базе данных."""

import asyncio
import os
import sys
from pathlib import Path

os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ftp_proxy', None)
os.environ.pop('all_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg
from src.config import settings


async def main():
    """Проверка эмбеддингов в базе данных."""
    print("="*80)
    print("ПРОВЕРКА ЭМБЕДДИНГОВ В БАЗЕ ДАННЫХ")
    print("="*80)

    conn = await asyncpg.connect(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password
    )

    try:
        # Проверка размерности эмбеддингов
        print("\n1. Проверка размерности эмбеддингов:")
        result = await conn.fetchrow("""
            SELECT
                vector_dims(embedding) as dimension,
                content,
                source_document
            FROM knowledge_base_chunks
            WHERE embedding IS NOT NULL
            LIMIT 1
        """)

        if result:
            print(f"   Размерность: {result['dimension']}")
            print(f"   Источник: {result['source_document']}")
            print(f"   Контент: {result['content'][:100]}...")
        else:
            print("   ❌ Не найдено записей с эмбеддингами!")
            return

        # Статистика эмбеддингов
        print("\n2. Статистика эмбеддингов:")
        stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_records,
                COUNT(embedding) as records_with_embeddings,
                COUNT(*) - COUNT(embedding) as records_without_embeddings
            FROM knowledge_base_chunks
        """)
        print(f"   Всего записей: {stats['total_records']}")
        print(f"   С эмбеддингами: {stats['records_with_embeddings']}")
        print(f"   Без эмбеддингов: {stats['records_without_embeddings']}")

        # Проверка значений эмбеддинга
        print("\n3. Проверка значений первого эмбеддинга:")
        embedding_sample = await conn.fetchrow("""
            SELECT embedding::text
            FROM knowledge_base_chunks
            WHERE embedding IS NOT NULL
            LIMIT 1
        """)

        if embedding_sample:
            emb_str = embedding_sample['embedding']
            # Берём первые 10 значений
            values = emb_str.strip('[]').split(',')[:10]
            print(f"   Первые 10 значений: {', '.join(v.strip() for v in values)}")

            # Проверяем не все ли нули
            try:
                float_values = [float(v.strip()) for v in values]
                if all(v == 0.0 for v in float_values):
                    print("   ⚠️ ВНИМАНИЕ: Все значения равны нулю!")
                else:
                    print("   ✅ Значения не нулевые")
            except:
                print("   ⚠️ Не удалось преобразовать значения в числа")

        # Тест самосхожести (должно быть близко к 1.0)
        print("\n4. Тест самосхожести (документ с самим собой):")
        self_similarity = await conn.fetchrow("""
            WITH sample AS (
                SELECT id, embedding
                FROM knowledge_base_chunks
                WHERE embedding IS NOT NULL
                LIMIT 1
            )
            SELECT
                1 - (a.embedding <=> b.embedding) as similarity
            FROM sample a, sample b
            WHERE a.id = b.id
        """)

        if self_similarity:
            sim = float(self_similarity['similarity'])
            print(f"   Схожесть: {sim:.6f}")
            if sim > 0.99:
                print("   ✅ Самосхожесть корректна")
            else:
                print(f"   ⚠️ ПРОБЛЕМА: Самосхожесть должна быть ~1.0, получено {sim}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
