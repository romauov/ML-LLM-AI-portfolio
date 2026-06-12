import json
import os
import re

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

from app.db.db import build_db_url
from app.db.sqlalchemy_models import SourceDocument, KnowledgeBaseChunk, Images
from app.llm.providers.llm_provider import LLMProvider
from knowledge.parsing_piplines.fattening_pigs_practical_guide.constants import SOURCE_DOCUMENT, CHAPTERS, JSON_BOOK, \
    EXCLUDED_PAGES, IMAGES_PATH
from knowledge.utils.common import natural_sort_key


def _get_chapter(page_number):
    for (start, end), value in CHAPTERS.items():
        if start <= page_number < end:
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
    """
    Добавление сущности `источник документа` в базу данных по книге
    Откорм свиней. Практическое руководство по росту, здоровью и поведению животных
    """

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    document = SourceDocument(
        name=SOURCE_DOCUMENT,
        language='ru',
        contents='\n'.join(CHAPTERS.values()),
    )

    session.add(document)

    _safety_commit(session)


def add_chunks():
    """Основная функция для обработки текстовых фрагментов, их векторизации и сохранения в базу данных."""

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    llm_provider = LLMProvider()

    with open(JSON_BOOK, "r", encoding='utf-8') as f:
        data = json.load(f)

    # получение source_document_id из базы по названию источника
    stmt = select(SourceDocument.id).where(SourceDocument.name.match(SOURCE_DOCUMENT))
    source_document_id = session.execute(stmt).fetchone()[0]

    for page in data['pages']:
        page_number = page.get('index') + 1

        if page_number in EXCLUDED_PAGES:
            continue

        chapter_title = _get_chapter(page_number)
        content = page.get('markdown')
        content = re.sub('(\\n|)\!\[img-\d{1,3}\.jpeg\]\(img-\d{1,3}\.jpeg\)', '', content)

        try:
            print('Обработка чанка', page_number)
            embedding = llm_provider.vectorize(content)
            new_chunk = KnowledgeBaseChunk(
                content=content,
                content_type='text',
                content_name=None,
                embedding=embedding,
                page_number=page_number,
                chunk_number=page_number,
                chapter_title=chapter_title,
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

    stmt = select(KnowledgeBaseChunk.id).where(
        KnowledgeBaseChunk.source_document_id == str(source_document_id_)
    ).order_by(KnowledgeBaseChunk.id.asc())
    chunk_ids = [row[0] for row in session.execute(stmt).fetchall()]

    for i, image_path in enumerate(sorted(os.listdir(IMAGES_PATH), key=natural_sort_key)):
        try:
            with open(os.path.join(IMAGES_PATH, image_path), "rb") as image_file:
                binary_image_data = image_file.read()

            image_ = Images(
                chunk_id=chunk_ids[i],
                source_document=SOURCE_DOCUMENT,
                image_data=binary_image_data
            )

            session.add(image_)
        except Exception as e:
            print(f"[ERROR] Не удалось обработать изображение: {e}")
            session.rollback()
            continue

    _safety_commit(session)
