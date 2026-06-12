import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import KnowledgeBaseChunk
from app.llm.providers.llm_provider import LLMProvider
from knowledge.utils.book_splitter.book_splitter import BookSplitter
from knowledge.parsing_piplines.peisak_disease_of_pigs.constants import JSON_BOOK, CHAPTERS, EXCLUDED_PAGES, \
    SOURCE_DOCUMENT


def get_chapter(page_number):
    for (start, end), value in CHAPTERS.items():
        if start <= page_number < end:
            return value


def process_chunks():
    """
    Основная функция для обработки текстовых фрагментов, их векторизации
    и сохранения в базу данных.
    """

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    llm_provider = LLMProvider()
    with open(JSON_BOOK, "r", encoding='utf-8') as f:
        data = json.load(f)

    pages = [page for page in data['pages'] if page.get('index') + 1 not in EXCLUDED_PAGES]

    splitter = BookSplitter(
        pages=pages,
        table_description_regex='(Таб\. \d{1,3}|Таблица\. \d{1,3}|Пример \d{1,3}:|Таблица \d{1,3})',
        image_description_regex='(Рис\. \d{1,3}|Рис\.\d{1,3})',
        to_drop_line_regex='(Продолжение таб\. \d{1,3}|Таб\. \d{1,3}: Продолжение)',
    )

    texts, tables, images = (splitter
                             .before_delete_newlines_symbol_at_table_cells()
                             .extract_table()
                             .extract_image()
                             .extract_text()
                             .after_combine_single_table_separated_by_diff_pages()
                             .after_combine_single_text_separated_by_diff_pages()
                             .after_split_text_chunks()
                             .after_get_chunks())

    for chunk_number, chunk in enumerate([*texts, *tables, *images], start=1):
        try:
            print('Обработка чанка', chunk_number)
            embedding = llm_provider.vectorize(chunk['content'])
            new_chunk = KnowledgeBaseChunk(
                content=chunk['content'],
                content_type=chunk['type'],
                content_name=chunk.get('name', None),
                embedding=embedding,
                page_number=chunk['page_number'],
                chunk_number=chunk_number,
                chapter_title=get_chapter(chunk['page_number']),
                source_document=SOURCE_DOCUMENT
            )
            session.add(new_chunk)

        except Exception as e:
            print(f"[ERROR] Не удалось обработать страницу: {e}")
            session.rollback()
            continue

    print("Сохранение всех изменений в базе данных...")
    try:
        session.commit()
        print("...изменения успешно сохранены.")
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
        print("...сессия с БД закрыта.")
