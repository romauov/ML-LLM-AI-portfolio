import json
import os

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker, Session

from app.db.db import build_db_url
from app.db.sqlalchemy_models import SourceDocument, KnowledgeBaseChunk, Images
from app.llm.providers.llm_provider import LLMProvider
from knowledge.utils.book_splitter.book_splitter import BookSplitter
from knowledge.parsing_piplines.diseases_of_poultry.constants import SOURCE_DOCUMENT, CHAPTERS, JSON_BOOK_1, \
    JSON_BOOK_2, EXCLUDED_PAGES, IMAGES_PATH
from knowledge.utils.common import natural_sort_key


def _get_chapter(page_number):
    for (start, end), value in CHAPTERS.items():
        if start <= page_number - 28 < end:
            return value


def _safety_commit(session: Session):
    try:
        session.commit()
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()


def add_source():
    """Добавление сущности `источник документа` в базу данных по книге Diseases of Poultry"""

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    document = SourceDocument(
        name=SOURCE_DOCUMENT,
        language='en',
        contents='\n'.join(CHAPTERS.values()),
    )

    session.add(document)

    _safety_commit(session)


def add_chunks():
    """Основная функция для обработки текстовых фрагментов, их векторизации и сохранения в базу данных."""

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    llm_provider = LLMProvider()

    with open(JSON_BOOK_1, "r", encoding='utf-8') as f:
        data_part_one = json.load(f)

    with open(JSON_BOOK_2, "r", encoding='utf-8') as f:
        data_part_two = json.load(f)

    for item in data_part_two['pages']:
        item['index'] = item['index'] + 700

    pages = []
    for page_number, page in enumerate([*data_part_one['pages'], *data_part_two['pages']]):
        if page_number not in EXCLUDED_PAGES:
            pages.append(page)

    splitter = BookSplitter(
        pages=pages,
        table_description_regex='(?<!\()Table \d+\.\d+',
        image_description_regex='(?<!\()Figure \d+\.\d+',
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

    # получение source_document_id из базы по названию источника
    stmt = select(SourceDocument.id).where(SourceDocument.name.match(SOURCE_DOCUMENT))
    source_document_id = session.execute(stmt).fetchone()[0]
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
                chapter_title=_get_chapter(chunk['page_number']),
                source_document_id=source_document_id
            )
            session.add(new_chunk)

        except Exception as e:
            print(f"[ERROR] Не удалось обработать страницу: {e}")
            session.rollback()
            continue

    _safety_commit(session)


def add_images():
    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    stmt = select(SourceDocument.id).where(SourceDocument.name.match(SOURCE_DOCUMENT))
    source_document_id_ = session.execute(stmt).fetchone()[0]

    stmt = select(KnowledgeBaseChunk.id).where(and_(
        KnowledgeBaseChunk.source_document_id == source_document_id_,
        KnowledgeBaseChunk.content_type.match('figure')
    )).order_by(KnowledgeBaseChunk.id.asc())
    figure_ids = [row[0] for row in session.execute(stmt).fetchall()]

    for i, image_path in enumerate(sorted(os.listdir(IMAGES_PATH), key=natural_sort_key)):
        try:
            with open(os.path.join(IMAGES_PATH, image_path), "rb") as image_file:
                binary_image_data = image_file.read()

            image_ = Images(
                chunk_id=figure_ids[i],
                source_document=SOURCE_DOCUMENT,
                image_data=binary_image_data
            )

            session.add(image_)
        except Exception as e:
            print(f"[ERROR] Не удалось обработать изображение: {e}")
            session.rollback()
            continue

    _safety_commit(session)
