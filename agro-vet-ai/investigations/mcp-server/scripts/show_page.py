"""Скрипт для просмотра содержимого страницы из базы знаний."""

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


async def main():
    """Показать содержимое страницы из базы знаний."""
    kb = KnowledgeBase()

    try:
        await kb.connect()
        print("=" * 80)
        print("Подключение к базе данных установлено")
        print("=" * 80)

        # Получаем список источников
        sources = await kb.get_sources()

        # Выбираем источник "Болезни свиней" (русскоязычный)
        source = None
        for s in sources:
            if "Болезни свиней" in s['source_document']:
                source = s
                break

        if not source:
            source = sources[0]  # Берём первый доступный

        print(f"\nИсточник: {source['source_document']}")
        print(f"Диапазон страниц: {source['page_range']}")

        # Получаем первую доступную страницу
        min_page = int(source['page_range'].split('-')[0])

        print(f"\n" + "=" * 80)
        print(f"Получение страницы {min_page} из источника")
        print("=" * 80)

        result = await kb.get_pages(source['source_document'], page_start=min_page)

        page = result['pages'][0]

        print(f"\n📄 Страница: {page['page_number']}")
        print(f"📖 Глава: {page['chapter_title']}")
        print(f"📏 Длина контента: {len(page['content'])} символов")
        print("\n" + "=" * 80)
        print("СОДЕРЖИМОЕ СТРАНИЦЫ:")
        print("=" * 80)
        print(page['content'])
        print("\n" + "=" * 80)

        # Получаем ещё одну страницу с бОльшим контентом
        print(f"\nПолучение страницы {min_page + 10} (для примера с большим контентом)")
        print("=" * 80)

        result2 = await kb.get_pages(source['source_document'], page_start=min_page + 10)
        if result2['pages']:
            page2 = result2['pages'][0]
            print(f"\n📄 Страница: {page2['page_number']}")
            print(f"📖 Глава: {page2['chapter_title']}")
            print(f"📏 Длина контента: {len(page2['content'])} символов")
            print("\n" + "=" * 80)
            print("СОДЕРЖИМОЕ СТРАНИЦЫ:")
            print("=" * 80)
            print(page2['content'][:2000])  # Показываем первые 2000 символов
            if len(page2['content']) > 2000:
                print("\n... (контент обрезан для отображения) ...")
            print("\n" + "=" * 80)

    finally:
        await kb.close()
        print("\nСоединение закрыто")


if __name__ == "__main__":
    asyncio.run(main())
