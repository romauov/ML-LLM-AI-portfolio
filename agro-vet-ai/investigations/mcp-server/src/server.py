"""MCP сервер для доступа к базе знаний VetRetro.

Предоставляет инструменты для семантического поиска и навигации
по ветеринарной базе знаний через Model Context Protocol.
"""

import os
from typing import Any

# Удаление переменных окружения прокси для корректной работы OpenAI API
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('ftp_proxy', None)
os.environ.pop('all_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)

from mcp.server import Server
from mcp.types import Tool, TextContent

from .knowledge_base import get_knowledge_base
from .document_extractor import get_document_extractor

import logging

logger = logging.getLogger(__name__)

# Создание MCP сервера
app = Server("vetretro-knowledge-base")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Список доступных инструментов MCP сервера."""
    return [
        Tool(
            name="vet_search",
            description=(
                "Семантический поиск по ветеринарной базе знаний. "
                "Ищет релевантную информацию в научных источниках "
                "по запросу на естественном языке."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос на естественном языке"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Максимальное количество результатов (по умолчанию 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Количество результатов для пропуска (пагинация, по умолчанию 0)",
                        "default": 0,
                        "minimum": 0
                    },
                    "source_filter": {
                        "type": "string",
                        "description": "Фильтр по источнику документа (опционально)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="vet_sources",
            description=(
                "Получить список всех доступных источников в базе знаний "
                "с их описаниями, диапазонами страниц и количеством глав."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="source_info",
            description=(
                "Получить детальную информацию об источнике, включая "
                "оглавление (список глав с диапазонами страниц)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source_document": {
                        "type": "string",
                        "description": "Название источника документа"
                    }
                },
                "required": ["source_document"]
            }
        ),
        Tool(
            name="get_pages",
            description=(
                "Получить контент с конкретных страниц источника. "
                "Можно запросить одну страницу или диапазон страниц."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source_document": {
                        "type": "string",
                        "description": "Название источника документа"
                    },
                    "page_start": {
                        "type": "integer",
                        "description": "Начальная страница",
                        "minimum": 1
                    },
                    "page_end": {
                        "type": "integer",
                        "description": "Конечная страница (опционально, если не указана - только page_start)",
                        "minimum": 1
                    }
                },
                "required": ["source_document", "page_start"]
            }
        ),
        Tool(
            name="extract_document",
            description=(
                "Извлечение текста из документов (PDF, DOCX) с использованием VseGPT API. "
                "Используйте для обработки лабораторных результатов, договоров, отчетов. "
                "PDF документы обрабатываются с OCR, что обеспечивает высокое качество "
                "распознавания таблиц и структурированных данных. "
                "Поддерживаемые форматы: PDF, DOCX. "
                "Результаты сохраняются в директорию extracted_documents/ - каждая страница "
                "в отдельном MD файле, изображения извлекаются в ту же папку."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Абсолютный путь к файлу (PDF или DOCX)"
                    }
                },
                "required": ["file_path"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Обработчик вызовов инструментов."""
    try:
        kb = await get_knowledge_base()

        if name == "vet_search":
            return await handle_vet_search(kb, arguments)
        elif name == "vet_sources":
            return await handle_vet_sources(kb, arguments)
        elif name == "source_info":
            return await handle_source_info(kb, arguments)
        elif name == "get_pages":
            return await handle_get_pages(kb, arguments)
        elif name == "extract_document":
            return await handle_extract_document(arguments)
        else:
            raise ValueError(f"Неизвестный инструмент: {name}")

    except Exception as e:
        error_message = str(e)
        logger.error(f"Ошибка при вызове инструмента {name}: {error_message}")

        # Форматируем сообщение об ошибке для пользователя
        user_message = f"❌ Ошибка при выполнении {name}:\n\n{error_message}"

        # Добавляем подсказку для частых ошибок
        if "subscription end" in error_message.lower() or "account are freezed" in error_message.lower():
            user_message += "\n\n💡 **Возможное решение:** Проверьте статус API ключа и при необходимости обновите его в конфигурации сервера."
        elif "api" in error_message.lower() and "error" in error_message.lower():
            user_message += "\n\n💡 **Подсказка:** Проверьте доступность API и корректность настроек подключения."

        return [TextContent(
            type="text",
            text=user_message
        )]


async def handle_vet_search(kb, arguments: dict) -> list[TextContent]:
    """Обработчик инструмента vet_search."""
    query = arguments.get("query")
    limit = arguments.get("limit", 5)
    offset = arguments.get("offset", 0)
    source_filter = arguments.get("source_filter")

    logger.info(
        f"Поиск: query='{query[:50]}...', limit={limit}, offset={offset}, "
        f"source_filter={source_filter}"
    )

    search_result = await kb.search(
        query=query,
        limit=limit,
        offset=offset,
        source_filter=source_filter,
        include_stats=True  # Всегда включаем статистику
    )

    results = search_result["results"]
    stats = search_result["stats"]

    if not results:
        return [TextContent(
            type="text",
            text="Результаты не найдены. Попробуйте изменить запрос или снизить требования к релевантности."
        )]

    # Форматирование результатов
    output = ""

    # Добавляем статистику если есть
    if stats:
        output += f"**Статистика поиска:**\n"
        output += f"- Всего найдено: {stats['total_found']} результатов\n"
        output += f"- Возвращено: {stats['returned']} (offset={offset}, limit={limit})\n"
        output += f"- Диапазон схожести: {stats['similarity_range']['min']:.3f} - {stats['similarity_range']['max']:.3f}\n"
        output += f"\n**Распределение по источникам:**\n"
        for source, count in stats['by_source'].items():
            output += f"- {source}: {count} результат(ов)\n"
        output += "\n---\n\n"
    else:
        output += f"Найдено результатов: {len(results)}\n\n"

    for i, result in enumerate(results, 1):
        result_num = offset + i
        output += f"## Результат {result_num}\n\n"
        output += f"**Источник:** {result['source_document']}\n"
        output += f"**Страница:** {result['page_number']}\n"

        if result.get('chapter_title'):
            output += f"**Глава:** {result['chapter_title']}\n"

        output += f"**Схожесть:** {result['similarity_score']:.3f}\n\n"

        if result.get('content_type') and result['content_type'] != 'text':
            output += f"**Тип контента:** {result['content_type']}\n"

        if result.get('content_name'):
            output += f"**Название:** {result['content_name']}\n\n"

        output += f"**Фрагмент страницы:**\n{result['content']}\n\n"

        if result.get('keywords') and result['keywords']:
            keywords_str = ", ".join(result['keywords'][:10])  # Первые 10 ключевых слов
            output += f"**Ключевые слова:** {keywords_str}\n\n"

        output += "---\n\n"

    return [TextContent(type="text", text=output)]


async def handle_vet_sources(kb, arguments: dict) -> list[TextContent]:
    """Обработчик инструмента vet_sources."""
    logger.info("Получение списка источников")

    sources = await kb.get_sources()

    if not sources:
        return [TextContent(
            type="text",
            text="Источники не найдены в базе знаний."
        )]

    # Форматирование результатов
    output = f"Всего источников в базе знаний: {len(sources)}\n\n"

    for i, source in enumerate(sources, 1):
        output += f"## {i}. {source['source_document']}\n\n"
        output += f"**Описание:** {source['description']}\n\n"
        output += f"**Диапазон страниц:** {source['page_range']}\n"
        output += f"**Количество глав:** {source['chapters_count']}\n\n"
        output += "---\n\n"

    return [TextContent(type="text", text=output)]


async def handle_source_info(kb, arguments: dict) -> list[TextContent]:
    """Обработчик инструмента source_info."""
    source_document = arguments.get("source_document")

    logger.info(f"Получение информации об источнике: {source_document}")

    info = await kb.get_source_info(source_document)

    # Форматирование результатов
    output = f"# {info['source_document']}\n\n"
    output += f"**Диапазон страниц:** {info['page_range']}\n"
    output += f"**Количество глав:** {len(info['chapters'])}\n\n"

    if info['chapters']:
        output += "## Оглавление\n\n"
        for i, chapter in enumerate(info['chapters'], 1):
            output += f"{i}. **{chapter['chapter_title']}** "
            output += f"(стр. {chapter['page_range']})\n"

    return [TextContent(type="text", text=output)]


async def handle_get_pages(kb, arguments: dict) -> list[TextContent]:
    """Обработчик инструмента get_pages."""
    source_document = arguments.get("source_document")
    page_start = arguments.get("page_start")
    page_end = arguments.get("page_end")

    logger.info(
        f"Получение страниц: source='{source_document}', "
        f"pages={page_start}-{page_end or page_start}"
    )

    result = await kb.get_pages(
        source_document=source_document,
        page_start=page_start,
        page_end=page_end
    )

    # Форматирование результатов
    output = f"# {result['source_document']}\n\n"
    output += f"**Запрошенные страницы:** {result['page_range']}\n"
    output += f"**Получено страниц:** {len(result['pages'])}\n\n"

    for page in result['pages']:
        output += f"## Страница {page['page_number']}\n\n"

        if page.get('chapter_title'):
            output += f"**Глава:** {page['chapter_title']}\n\n"

        output += page['content']
        output += "\n\n---\n\n"

    return [TextContent(type="text", text=output)]


async def handle_extract_document(arguments: dict) -> list[TextContent]:
    """Обработчик инструмента extract_document."""
    file_path = arguments.get("file_path")

    logger.info(f"Извлечение текста из документа: {file_path}")

    extractor = get_document_extractor()
    result = await extractor.extract_text(file_path)

    if not result["success"]:
        # Ошибка при извлечении
        error_output = f"❌ **Ошибка при извлечении текста из документа**\n\n"
        error_output += f"**Файл:** {result['metadata'].get('filename', 'неизвестно')}\n\n"
        error_output += f"**Ошибка:** {result['error']}\n"

        return [TextContent(type="text", text=error_output)]

    # Успешное извлечение
    metadata = result["metadata"]
    filename = metadata.get("filename", "документ")

    output = f"# 📄 Текст извлечен из документа: {filename}\n\n"

    # Информация о сохраненных файлах
    if "output_dir" in metadata:
        output += "## Сохраненные файлы\n\n"
        output += f"**Директория:** `{metadata['output_dir']}`\n\n"

        if "saved_pages" in metadata:
            output += f"**Страницы:** {len(metadata['saved_pages'])} файлов\n"
            for page_file in metadata['saved_pages'][:5]:  # Показываем первые 5
                output += f"- `{page_file}`\n"
            if len(metadata['saved_pages']) > 5:
                output += f"- ... и еще {len(metadata['saved_pages']) - 5}\n"
            output += "\n"

        if "saved_images" in metadata and metadata['saved_images']:
            output += f"**Изображения:** {len(metadata['saved_images'])} файлов\n"
            for img_file in metadata['saved_images'][:5]:  # Показываем первые 5
                output += f"- `{img_file}`\n"
            if len(metadata['saved_images']) > 5:
                output += f"- ... и еще {len(metadata['saved_images']) - 5}\n"
            output += "\n"

    # Краткое содержимое (первые 1000 символов)
    output += "## Краткое содержимое\n\n"
    preview = result["text"][:1000]
    if len(result["text"]) > 1000:
        preview += "\n\n*[...продолжение в сохраненных файлах]*"
    output += preview
    output += "\n\n---\n\n"

    # Метаданные
    output += "## Метаданные\n\n"
    output += f"**Размер файла:** {metadata.get('file_size_bytes', 0) / 1024:.1f} KB\n"
    output += f"**Модель:** {metadata.get('model_used', 'неизвестно')}\n"

    if "pages_processed" in metadata:
        output += f"**Обработано страниц:** {metadata['pages_processed']}\n"

    if metadata.get("has_images"):
        output += f"**Извлечено изображений:** {metadata.get('images_count', 0)}\n"

    logger.info(
        f"Текст успешно извлечен из {filename}: "
        f"{len(result['text'])} символов, "
        f"сохранено в {metadata.get('output_dir', 'N/A')}"
    )

    return [TextContent(type="text", text=output)]


# Функция main() перенесена в server_stdio.py и server_http.py
# для запуска через разные транспорты
