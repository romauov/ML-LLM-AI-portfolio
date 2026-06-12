#!/usr/bin/env python3
"""Диагностика качества эмбеддингов в базе данных.

Проверяет:
1. Размерность эмбеддингов в БД
2. Не являются ли они нулевыми/пустыми
3. Самоподобие (один и тот же текст должен иметь distance ≈ 0)
4. Сравнение эмбеддингов из БД с новыми эмбеддингами того же текста
"""

import asyncio
import sys
from pathlib import Path

# Добавляем родительскую папку в путь поиска модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge_base import get_knowledge_base
from src.embeddings import get_embeddings_generator


async def main():
    print("=== Диагностика эмбеддингов ===\n")

    kb = await get_knowledge_base()
    emb_gen = get_embeddings_generator()

    try:
        # 1. Проверка размерности и наличия данных
        print("1. Проверка эмбеддингов в БД...")
        sql = """
            SELECT
                content,
                source_document,
                page_number,
                embedding,
                vector_dims(embedding) as dimension
            FROM knowledge_base_chunks
            WHERE embedding IS NOT NULL
            LIMIT 5
        """

        async with kb.pool.acquire() as conn:
            rows = await conn.fetch(sql)

        print(f"   Найдено строк с эмбеддингами: {len(rows)}")
        if rows:
            for i, row in enumerate(rows):
                dim = row["dimension"]
                content_preview = row["content"][:80].replace('\n', ' ')
                print(f"   [{i+1}] Размерность: {dim}, Контент: {content_preview}...")

                # Проверяем, не нулевой ли эмбеддинг
                embedding = row["embedding"]
                # Эмбеддинг приходит как строка "[0.123, 0.456, ...]"
                embedding_str = str(embedding)
                print(f"       Тип: {type(embedding).__name__}")
                print(f"       Первые 100 символов: {embedding_str[:100]}...")

        print()

        # 2. Тест самоподобия - берем текст из БД и генерируем эмбеддинг
        print("2. Тест самоподобия (один текст дважды)...")
        test_row = rows[0]
        test_text = test_row["content"]

        print(f"   Тестовый текст (первые 100 символов):")
        print(f"   {test_text[:100].replace(chr(10), ' ')}...")
        print()

        # Генерируем эмбеддинг для того же текста
        print("   Генерация эмбеддинга через API...")
        new_embedding = await emb_gen.generate_embedding(test_text)

        print(f"   Размерность нового эмбеддинга: {len(new_embedding)}")
        print(f"   Первые 5 значений: {new_embedding[:5]}")
        print()

        # Сравниваем с эмбеддингом из БД
        print("   Сравнение с эмбеддингом из БД...")
        embedding_str = "[" + ", ".join(f"{x:.10f}" for x in new_embedding) + "]"

        sql_compare = f"""
            SELECT
                embedding <=> '{embedding_str}' as distance_to_new,
                vector_dims(embedding) as dimension
            FROM knowledge_base_chunks
            WHERE content = $1
            LIMIT 1
        """

        async with kb.pool.acquire() as conn:
            result = await conn.fetchrow(sql_compare, test_text)

        if result:
            distance = result["distance_to_new"]
            print(f"   Distance между БД и новым эмбеддингом: {distance:.6f}")

            if distance < 0.01:
                print("   ✅ ОТЛИЧНО: Эмбеддинги почти идентичны (distance < 0.01)")
            elif distance < 0.1:
                print("   ⚠️  ВНИМАНИЕ: Небольшое расхождение (0.01 < distance < 0.1)")
            else:
                print("   ❌ ПРОБЛЕМА: Большое расхождение (distance > 0.1)")
                print("      Возможно, эмбеддинги в БД были созданы другой моделью!")

        print()

        # 3. Тест самоподобия - один текст через API дважды
        print("3. Тест стабильности API (один текст дважды через API)...")
        embedding1 = await emb_gen.generate_embedding(test_text)
        embedding2 = await emb_gen.generate_embedding(test_text)

        embedding1_str = "[" + ", ".join(f"{x:.10f}" for x in embedding1) + "]"
        embedding2_str = "[" + ", ".join(f"{x:.10f}" for x in embedding2) + "]"

        sql_self = f"""
            SELECT '{embedding1_str}'::vector <=> '{embedding2_str}'::vector as distance
        """

        async with kb.pool.acquire() as conn:
            result = await conn.fetchrow(sql_self)

        self_distance = result["distance"]
        print(f"   Distance между двумя генерациями: {self_distance:.10f}")

        if self_distance < 0.0001:
            print("   ✅ API стабилен: distance ≈ 0")
        else:
            print(f"   ⚠️  API нестабилен: distance = {self_distance}")

        print()

        # 4. Проверка на типичный запрос
        print("4. Тест на реальный запрос...")
        query = "антибактериальная терапия"
        print(f"   Запрос: '{query}'")

        results = await kb.search(query, top_k=3)
        print(f"   Результатов после фильтрации: {len(results)}")

        if results:
            for i, res in enumerate(results):
                print(f"   [{i+1}] Distance: {res['distance']:.6f}, "
                      f"Similarity: {res['similarity_score']:.6f}")
                print(f"       {res['content'][:80].replace(chr(10), ' ')}...")
        else:
            print("   ⚠️  Ни одного результата не прошло фильтр!")

            # Попробуем без фильтра
            print("\n   Попытка поиска с высоким порогом (2.0)...")
            query_embedding = await emb_gen.generate_embedding(query)
            embedding_str = "[" + ", ".join(f"{x:.10f}" for x in query_embedding) + "]"

            sql = f"""
                SELECT
                    content,
                    embedding <=> '{embedding_str}' as distance
                FROM knowledge_base_chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> '{embedding_str}' ASC
                LIMIT 5
            """

            async with kb.pool.acquire() as conn:
                rows = await conn.fetch(sql)

            print(f"   Топ-5 ближайших результатов (без фильтра):")
            for i, row in enumerate(rows):
                print(f"   [{i+1}] Distance: {row['distance']:.6f}")
                print(f"       {row['content'][:80].replace(chr(10), ' ')}...")

    finally:
        await kb.close()
        await emb_gen.close()


if __name__ == "__main__":
    asyncio.run(main())
