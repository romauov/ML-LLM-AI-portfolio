"""Тесты для MCP инструментов сервера."""

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

from src.server import (
    handle_vet_search,
    handle_vet_sources,
    handle_source_info,
    handle_get_pages
)
from src.knowledge_base import KnowledgeBase


async def test_vet_sources():
    """Тест инструмента vet_sources."""
    print("\n" + "=" * 80)
    print("ТЕСТ 1: vet_sources - получение списка источников")
    print("=" * 80)

    kb = KnowledgeBase()
    await kb.connect()

    try:
        arguments = {}
        result = await handle_vet_sources(kb, arguments)

        assert len(result) == 1, "Должен вернуться один TextContent объект"
        text = result[0].text

        print("\nРезультат:")
        print(text[:500])  # Первые 500 символов
        print("...")

        # Проверки
        assert "Всего источников" in text, "Должна быть информация о количестве источников"
        assert "Болезни свиней" in text or "Antimicrobial" in text, "Должны быть названия источников"

        print("\n✅ Тест vet_sources пройден успешно")

    finally:
        await kb.close()


async def test_source_info():
    """Тест инструмента source_info."""
    print("\n" + "=" * 80)
    print("ТЕСТ 2: source_info - информация об источнике")
    print("=" * 80)

    kb = KnowledgeBase()
    await kb.connect()

    try:
        # Сначала получаем список источников
        sources = await kb.get_sources()
        first_source = sources[0]['source_document']

        arguments = {
            "source_document": first_source
        }
        result = await handle_source_info(kb, arguments)

        assert len(result) == 1, "Должен вернуться один TextContent объект"
        text = result[0].text

        print(f"\nИсточник: {first_source}")
        print("\nРезультат:")
        print(text[:800])  # Первые 800 символов
        print("...")

        # Проверки
        assert first_source in text, "Должно быть название источника"
        assert "Диапазон страниц" in text, "Должен быть диапазон страниц"
        assert "Оглавление" in text or "Количество глав" in text, "Должна быть информация о главах"

        print("\n✅ Тест source_info пройден успешно")

    finally:
        await kb.close()


async def test_get_pages():
    """Тест инструмента get_pages."""
    print("\n" + "=" * 80)
    print("ТЕСТ 3: get_pages - получение страниц")
    print("=" * 80)

    kb = KnowledgeBase()
    await kb.connect()

    try:
        # Получаем список источников для определения начальной страницы
        sources = await kb.get_sources()
        first_source = sources[0]['source_document']
        min_page = int(sources[0]['page_range'].split('-')[0])

        # Тест 1: Одна страница
        print(f"\nЗапрос страницы {min_page} из '{first_source}'")
        arguments = {
            "source_document": first_source,
            "page_start": min_page
        }
        result = await handle_get_pages(kb, arguments)

        assert len(result) == 1, "Должен вернуться один TextContent объект"
        text = result[0].text

        print("\nРезультат (первые 500 символов):")
        print(text[:500])
        print("...")

        # Проверки
        assert first_source in text, "Должно быть название источника"
        assert f"Страница {min_page}" in text, "Должен быть номер страницы"
        assert len(text) > 100, "Должен быть контент страницы"

        # Тест 2: Диапазон страниц
        print(f"\nЗапрос страниц {min_page}-{min_page+2}")
        arguments = {
            "source_document": first_source,
            "page_start": min_page,
            "page_end": min_page + 2
        }
        result = await handle_get_pages(kb, arguments)

        text = result[0].text
        assert f"Получено страниц: 3" in text or f"Страница {min_page+1}" in text, "Должно быть несколько страниц"

        print("\n✅ Тест get_pages пройден успешно")

    finally:
        await kb.close()


async def test_vet_search():
    """Тест инструмента vet_search."""
    print("\n" + "=" * 80)
    print("ТЕСТ 4: vet_search - семантический поиск")
    print("=" * 80)

    kb = KnowledgeBase()
    await kb.connect()

    try:
        # Тест на английском (больше контента в базе на английском)
        queries = [
            "antibiotic therapy swine",
            "E. coli infection treatment",
            "broiler health management"
        ]

        for query in queries:
            print(f"\nЗапрос: '{query}'")
            arguments = {
                "query": query,
                "limit": 3
            }
            result = await handle_vet_search(kb, arguments)

            assert len(result) == 1, "Должен вернуться один TextContent объект"
            text = result[0].text

            print("\nРезультат (первые 400 символов):")
            print(text[:400])
            print("...")

            # Базовые проверки
            assert len(text) > 50, "Должен быть текст результата"

            # Если нашлись результаты
            if "Результат 1" in text:
                assert "Источник:" in text, "Должна быть информация об источнике"
                assert "Страница:" in text, "Должен быть номер страницы"
                assert "Схожесть:" in text, "Должна быть оценка схожести"
                assert "Фрагмент страницы:" in text, "Должен быть фрагмент страницы"

                # Проверка статистики
                if "Статистика поиска:" in text:
                    assert "Всего найдено:" in text, "Должна быть статистика"
                    assert "Распределение по источникам:" in text, "Должно быть распределение"

                print("✅ Найдены результаты")
            else:
                print("⚠️  Результаты не найдены (схожесть ниже порога)")

        print("\n✅ Тест vet_search пройден успешно")

    finally:
        await kb.close()


async def main():
    """Запуск всех тестов."""
    print("=" * 80)
    print("ЗАПУСК ТЕСТОВ MCP ИНСТРУМЕНТОВ")
    print("=" * 80)

    try:
        await test_vet_sources()
        await test_source_info()
        await test_get_pages()
        await test_vet_search()

        print("\n" + "=" * 80)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ ТЕСТ ПРОВАЛИЛСЯ: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
