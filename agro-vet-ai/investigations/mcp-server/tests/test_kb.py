"""Тестовый скрипт для проверки работы KnowledgeBase."""

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
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.knowledge_base import KnowledgeBase

import logging

logger = logging.getLogger(__name__)


async def test_connection():
    """Тест подключения к базе данных."""
    logger.info("=" * 60)
    logger.info("Тест 1: Подключение к базе данных")
    logger.info("=" * 60)

    kb = KnowledgeBase()
    try:
        await kb.connect()
        logger.info("✅ Подключение успешно установлено")
        return kb
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        raise


async def test_get_sources(kb: KnowledgeBase):
    """Тест получения списка источников."""
    logger.info("\n" + "=" * 60)
    logger.info("Тест 2: Получение списка источников")
    logger.info("=" * 60)

    try:
        sources = await kb.get_sources()
        logger.info(f"✅ Найдено источников: {len(sources)}")

        for i, source in enumerate(sources, 1):
            logger.info(f"\nИсточник {i}:")
            logger.info(f"  Название: {source['source_document']}")
            logger.info(f"  Описание: {source['description'][:100]}...")
            logger.info(f"  Диапазон страниц: {source['page_range']}")
            logger.info(f"  Количество глав: {source['chapters_count']}")

        return sources
    except Exception as e:
        logger.error(f"❌ Ошибка получения источников: {e}")
        raise


async def test_get_source_info(kb: KnowledgeBase, source_name: str):
    """Тест получения информации об источнике."""
    logger.info("\n" + "=" * 60)
    logger.info(f"Тест 3: Информация об источнике")
    logger.info("=" * 60)

    try:
        info = await kb.get_source_info(source_name)
        logger.info(f"✅ Источник: {info['source_document']}")
        logger.info(f"   Диапазон страниц: {info['page_range']}")
        logger.info(f"   Количество глав: {len(info['chapters'])}")

        logger.info("\nПервые 5 глав:")
        for i, chapter in enumerate(info['chapters'][:5], 1):
            logger.info(f"  {i}. {chapter['chapter_title']} (стр. {chapter['page_range']})")

        return info
    except Exception as e:
        logger.error(f"❌ Ошибка получения информации об источнике: {e}")
        raise


async def test_search(kb: KnowledgeBase):
    """Тест семантического поиска."""
    logger.info("\n" + "=" * 60)
    logger.info("Тест 4: Семантический поиск")
    logger.info("=" * 60)

    queries = [
        "неонатальная диарея у поросят",
        "E.coli инфекция",
        "лечение антибиотиками",
    ]

    for query in queries:
        logger.info(f"\nЗапрос: '{query}'")
        try:
            search_result = await kb.search(query, limit=3, include_stats=True)
            results = search_result["results"]
            stats = search_result["stats"]

            logger.info(f"✅ Найдено результатов: {len(results)}")
            if stats:
                logger.info(f"  Всего в базе: {stats['total_found']}")
                logger.info(f"  Диапазон схожести: {stats['similarity_range']['min']:.3f} - {stats['similarity_range']['max']:.3f}")

            for i, result in enumerate(results, 1):
                logger.info(f"\nРезультат {i}:")
                logger.info(f"  Источник: {result['source_document']}")
                logger.info(f"  Страница: {result['page_number']}")
                logger.info(f"  Глава: {result['chapter_title']}")
                logger.info(f"  Схожесть: {result['similarity_score']:.3f}")
                logger.info(f"  Контент: {result['content'][:200]}...")
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            raise


async def test_get_pages(kb: KnowledgeBase, source_name: str, min_page: int):
    """Тест получения страниц."""
    logger.info("\n" + "=" * 60)
    logger.info("Тест 5: Получение страниц")
    logger.info("=" * 60)

    try:
        # Получаем одну страницу
        logger.info(f"\nПолучение страницы {min_page} из '{source_name}'")
        result = await kb.get_pages(source_name, page_start=min_page)
        logger.info(f"✅ Получено страниц: {len(result['pages'])}")

        page = result['pages'][0]
        logger.info(f"  Страница: {page['page_number']}")
        logger.info(f"  Глава: {page['chapter_title']}")
        logger.info(f"  Длина контента: {len(page['content'])} символов")
        logger.info(f"  Начало: {page['content'][:200]}...")

        # Получаем диапазон страниц
        logger.info(f"\nПолучение страниц {min_page}-{min_page + 2} из '{source_name}'")
        result = await kb.get_pages(source_name, page_start=min_page, page_end=min_page + 2)
        logger.info(f"✅ Получено страниц: {len(result['pages'])}")

        for page in result['pages']:
            logger.info(f"  Страница {page['page_number']}: {len(page['content'])} символов")

    except Exception as e:
        logger.error(f"❌ Ошибка получения страниц: {e}")
        raise


async def main():
    """Основная функция для запуска всех тестов."""
    logger.info("Запуск тестов KnowledgeBase")

    kb = None
    try:
        # Тест 1: Подключение
        kb = await test_connection()

        # Тест 2: Список источников
        sources = await test_get_sources(kb)

        if sources:
            # Используем первый источник для дальнейших тестов
            first_source = sources[0]['source_document']
            # Получаем минимальную страницу из диапазона
            min_page = int(sources[0]['page_range'].split('-')[0])

            # Тест 3: Информация об источнике
            await test_get_source_info(kb, first_source)

            # Тест 4: Семантический поиск
            await test_search(kb)

            # Тест 5: Получение страниц
            await test_get_pages(kb, first_source, min_page)

        logger.info("\n" + "=" * 60)
        logger.info("✅ Все тесты пройдены успешно!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"\n❌ Тесты завершились с ошибкой: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if kb:
            await kb.close()
            logger.info("Соединение с базой данных закрыто")


if __name__ == "__main__":
    asyncio.run(main())
