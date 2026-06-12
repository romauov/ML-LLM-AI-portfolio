"""Скрипт для проверки векторного поиска и оценки схожести."""

import asyncio
import os
import sys
from pathlib import Path

# Удаление переменных окружения прокси
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ftp_proxy', None)
os.environ.pop('all_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.knowledge_base import KnowledgeBase
from src.config import settings


async def test_search_with_threshold(query: str, threshold: float):
    """Тестирование поиска с разными порогами."""
    print(f"\n{'='*80}")
    print(f"Запрос: '{query}'")
    print(f"Порог схожести: {threshold}")
    print(f"{'='*80}")

    kb = KnowledgeBase()
    await kb.connect()

    try:
        # Временно изменяем порог
        original_threshold = settings.similarity_threshold
        settings.similarity_threshold = threshold

        results = await kb.search(query, top_k=10)

        settings.similarity_threshold = original_threshold

        if not results:
            print("❌ Результаты не найдены")
        else:
            print(f"✅ Найдено результатов: {len(results)}\n")
            for i, result in enumerate(results[:3], 1):  # Показываем первые 3
                print(f"Результат {i}:")
                print(f"  Схожесть: {result['similarity_score']:.4f}")
                print(f"  Источник: {result['source_document']}")
                print(f"  Страница: {result['page_number']}")
                print(f"  Глава: {result['chapter_title']}")
                print(f"  Контент: {result['content'][:200]}...")
                print()

    finally:
        await kb.close()


async def main():
    """Тестирование с разными запросами и порогами."""
    queries = [
        "антибиотики для свиней",
        "antibiotics for swine",
        "antimicrobial therapy",
        "E. coli treatment",
        "respiratory disease",
    ]

    thresholds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]

    print("="*80)
    print("ТЕСТИРОВАНИЕ ВЕКТОРНОГО ПОИСКА")
    print(f"Текущий порог в настройках: {settings.similarity_threshold}")
    print("="*80)

    # Тестируем каждый запрос с порогом 0.0 (все результаты)
    print("\n" + "="*80)
    print("ЭТАП 1: Проверка реальных значений схожести (порог = 0.0)")
    print("="*80)

    for query in queries:
        await test_search_with_threshold(query, 0.0)

    # Рекомендация
    print("\n" + "="*80)
    print("РЕКОМЕНДАЦИИ")
    print("="*80)
    print("На основе результатов выше, определите оптимальный порог схожести.")
    print("Для большинства запросов достаточно порога 0.15-0.20")


if __name__ == "__main__":
    asyncio.run(main())
