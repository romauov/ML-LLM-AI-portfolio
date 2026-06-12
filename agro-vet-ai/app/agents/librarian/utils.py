import base64
import re
import json


def find_table_and_figure_names(documents: list[dict]) -> tuple[list[str], list[str]]:
    """
    Поиск названий таблиц (Table 11.1) и фигур (Figure 1.11) в тексте.

    :param documents: Список документов.
    :return: Список уникальных названий таблиц, список уникальных названий фигур
    """
    table_regex = r'Table \d{1,3}\.\d{1,3}'
    figure_regex = r'(Figure \d{1,3}\.\d{1,3}|[Рр]ис\. \d{1,3}\.\d{1,3}\.\d{1,3})'
    table_names, figure_names = [], []
    for doc in documents:
        content = doc['content']
        tables = re.findall(table_regex, content)
        tables = [f"{table}." for table in tables]
        table_names.extend(tables)

        figures = re.findall(figure_regex, content)
        figures = [f"{figure}." for figure in figures]
        figure_names.extend(figures)

    return list(set(table_names)), list(set(figure_names))


def format_context(
        documents: list[dict],
        additional_context: dict = None
) -> str:
    """
    Форматирование документов:
        # Название главы
        ## Номер страницы
        ## Название раздела
        Текст раздела, таблица или описание изображения
    И дополнительного контекста.

    :param documents: Список документов.
    :param additional_context: Дополнительный контекст.
    :return: Отформатированная строка
    """

    context_parts = []
    if documents:
        deduplicated_documents = [dict(tuple_) for tuple_ in {tuple(doc.items()) for doc in documents}]
        sorted_documents = sorted(deduplicated_documents, key=lambda x: (x['page_number'] or 0, x['chunk_number'] or 0))

        last_chapter_title = None
        for document in sorted_documents:
            document_chapter = document['chapter_title']
            page_number = f"Номер страницы: {document['page_number']}"
            if last_chapter_title != document_chapter:
                last_chapter_title = document_chapter
                context_parts.append(f"Глава: {last_chapter_title}\n{page_number}\n{document['content']}")
            else:
                context_parts.append(f"{page_number}\n{document['content']}")

    # Добавляем дополнительный контекст
    if additional_context:
        context_parts.append("\nДополнительная информация:")
        for key, value in additional_context.items():
            context_parts.append(f"- {key}: {value}")

    return "\n\n".join(context_parts)


def fix_broken_tool_call(message):
    """Исправляет кривой вызов инструмента, перенося параметры из content в arguments."""

    # Проверяем, есть ли что исправлять
    if not message.tool_calls or not message.content:
        return message

    tool_call = message.tool_calls[0]

    # Пропускаем, если arguments уже валидны
    try:
        if json.loads(tool_call.function.arguments):
            return message
    except json.JSONDecodeError as e:
        pass

    tool_call.function.arguments = (message.content + tool_call.function.arguments).strip()
    message.content = ""

    return message


def memory_view_to_base64_str(memory_view: memoryview | bytes) -> str:
    image_bytes = memory_view # psycopg3 возвращает байты
    return base64.b64encode(image_bytes).decode('utf-8')