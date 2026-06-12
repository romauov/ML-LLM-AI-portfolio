import base64
import re


def find_table_and_figure_names(documents: list[dict]) -> tuple[list[str], list[str]]:
    """
    Поиск названий таблиц (Table 11.1) и фигур (Figure 1.11) в тексте.

    :param documents: Список документов.
    :return: Список уникальных названий таблиц, список уникальных названий фигур
    """
    table_regex = r"Table \d{1,3}\.\d{1,3}"
    figure_regex = r"(Figure \d{1,3}\.\d{1,3}|[Рр]ис\. \d{1,3}\.\d{1,3}\.\d{1,3})"
    table_names, figure_names = [], []
    for doc in documents:
        content = doc["content"]
        tables = re.findall(table_regex, content)
        tables = [f"{table}." for table in tables]
        table_names.extend(tables)

        figures = re.findall(figure_regex, content)
        figures = [f"{figure}." for figure in figures]
        figure_names.extend(figures)

    return list(set(table_names)), list(set(figure_names))


def format_context(documents: list[dict], additional_context: dict = None) -> str:
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
        deduplicated_documents = [
            dict(tuple_) for tuple_ in {tuple(doc.items()) for doc in documents}
        ]
        sorted_documents = sorted(
            deduplicated_documents,
            key=lambda x: (x["page_number"] or 0, x["chunk_number"] or 0),
        )

        last_chapter_title = None
        last_source = None
        for document in sorted_documents:
            document_chapter = document["chapter_title"]
            document_source = document.get("source_document", "Unknown")
            page_number = f"Страница {document['page_number']}"

            # Добавляем источник только если он изменился
            if last_source != document_source:
                last_source = document_source
                context_parts.append(f"📖 **{last_source}**")

            if last_chapter_title != document_chapter:
                last_chapter_title = document_chapter
                context_parts.append(
                    f"Глава: {last_chapter_title} | {page_number}\n{document['content']}"
                )
            else:
                context_parts.append(f"{page_number}\n{document['content']}")

    # Добавляем дополнительный контекст
    if additional_context:
        context_parts.append("\nДополнительная информация:")
        for key, value in additional_context.items():
            context_parts.append(f"- {key}: {value}")

    return "\n\n".join(context_parts)


def memory_view_to_base64_str(memory_view: memoryview | bytes) -> str:
    image_bytes = memory_view
    return base64.b64encode(image_bytes).decode("utf-8")
