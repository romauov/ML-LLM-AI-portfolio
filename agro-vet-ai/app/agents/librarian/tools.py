from langchain_core.tools import tool

from app.agents.librarian.utils import format_context, find_table_and_figure_names, memory_view_to_base64_str
from app.db.vector_search import VectorSearchEngine
from app.llm.providers.llm_provider import LLMProvider
from config.config import Config

cfg = Config.from_yaml()


@tool(parse_docstring=True)
def search_database_by_all_books(question_ru: str, question_en: str) -> dict:
    """
    Поиск релевантной информации из базы знаний по всем книгам.

    Args:
        question_ru: текстовый запрос на русском языке по которому осуществляется векторный поиск документов.
        question_en: текстовый запрос на английском языке по которому осуществляется векторный поиск документов.
    """

    search_engine = VectorSearchEngine()

    all_documents = []
    images = []
    for question, language in [(question_ru, 'ru'), (question_en, 'en')]:
        embedding_result = LLMProvider().vectorize(question)
        documents = search_engine.search_by_embedding(
            embedding=embedding_result.vector,
            embedding_column=embedding_result.column,
            content_types=['text', 'table'],
            limit=cfg.librarian.search.doc_limit,
            threshold=cfg.librarian.search.similarity_threshold,
            source_language=language
        )

        all_documents.extend(documents)
        images.extend([memory_view_to_base64_str(d['image']) for d in documents if d.get('image')])

    text = format_context(documents=all_documents)

    return {
        "text": text,
        "documents": all_documents,
        "images": images,
    }


@tool(parse_docstring=True)
def search_database_by_one_book(question: str, source_name: str) -> dict:
    """
    Поиск релевантной информации из базы знаний по одной книге.

    Args:
        question: текстовый запрос по которому осуществляется векторный поиск документов.
            Вопрос составляется на языке книги.
        source_name: название книги по кторой происходит поиск.
    """

    search_engine = VectorSearchEngine()

    embedding_result = LLMProvider().vectorize(question)
    documents = search_engine.search_by_embedding(
        embedding=embedding_result.vector,
        embedding_column=embedding_result.column,
        content_types=['text', 'table'],
        source_name=source_name,
        limit=cfg.librarian.search.doc_limit,
        threshold=cfg.librarian.search.similarity_threshold
    )

    images = [memory_view_to_base64_str(d['image']) for d in documents if d.get('image')]
    context_text = format_context(documents=documents)

    return {
        "text": context_text,
        "documents": documents,
        "images": images,
    }


@tool(parse_docstring=True)
def get_page_content(page_numbers: list[int], source_name: str) -> dict:
    """
    Получение полного содержимоого указанной страницы из книги в базе знаний
    Используется для проверки/расширения контекста уже найденной информации.

    Args:
        page_numbers: номера страниц.
        source_name: название книги по кторой происходит поиск.
    """

    search_engine = VectorSearchEngine()
    documents = search_engine.get_chunks_by_page_number(
        page_numbers=page_numbers,
        content_types=['text'],
        source_name=source_name,
    )

    tables_names, figures_names = find_table_and_figure_names(documents)
    if tables_names:
        tables = search_engine.get_tables_chunk(tables_names=tables_names, source_name=source_name)
        documents.extend(tables)
    if figures_names:
        figures = search_engine.get_figures_chunk(figures_names=figures_names, source_name=source_name)
        documents.extend(figures)

    context_text = format_context(documents=documents)
    images = [memory_view_to_base64_str(d['image']) for d in documents if d.get('image')]
    return {
        "text": context_text,
        "documents": documents,
        "images": images,
    }


@tool(parse_docstring=True)
def get_list_of_books() -> dict:
    """
    Получение списка доступных книг.
    """
    search_engine = VectorSearchEngine()
    book_names = search_engine.get_all_book_names()
    return {
        "text": '\n'.join(book_names),
    }


@tool(parse_docstring=True)
def get_books_content(sources_name: list[str]) -> dict:
    """
    Получение огалавления и языка книг по их названиям.
    Желательно получить оглавления только по нужным книгам, а не всем доступным.

    Args:
        sources_name: список с названиями книг для которых нyжна дополнительная мета информация.
    """

    search_engine = VectorSearchEngine()
    books_meta_info = search_engine.get_books_meta_info(sources_name)
    return {
        "text": str(books_meta_info),
    }
