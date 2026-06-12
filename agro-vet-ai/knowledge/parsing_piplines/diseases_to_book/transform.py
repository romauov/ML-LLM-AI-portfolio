import json
import os

import yaml
from langchain_text_splitters import MarkdownHeaderTextSplitter
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import KnowledgeBaseChunk, SourceDocument
from app.llm.providers.llm_provider import LLMProvider
from knowledge.utils.book_splitter.book_splitter import BookSplitter
from knowledge.parsing_piplines.diseases_to_book.constants import SWINE_PATH, AVIAN_PATH, SWINE_DOCUMENT_NAME, \
    AVIAN_DOCUMENT_NAME, AVIAN_CONTENTS


def _process_value(value):
    if isinstance(value, list):
        processed = [_process_value(item) for item in value]
        filtered = [str(item).strip() for item in processed]
        return ' '.join(filtered)
    elif isinstance(value, dict):
        parts = []
        for key, val in value.items():
            processed_val = _process_value(val)
            if processed_val:
                parts.append(f"{key}: {processed_val}")
        return '; '.join(parts)
    elif isinstance(value, str):
        return ' '.join(value.replace('\n', ' ').split())
    return str(value)


def _yaml_to_markdown(yaml_data):
    root_key = next(iter(yaml_data))
    sections = yaml_data[root_key]

    markdown_parts = []
    for section_name, content in sections.items():
        header = section_name.replace('_', ' ').capitalize()
        markdown_parts.append(f"## {header}")
        markdown_parts.append(_process_value(content).strip())
        markdown_parts.append('')

    return '\n'.join(markdown_parts)


def process_avian():
    source_path, source_name = AVIAN_PATH, AVIAN_DOCUMENT_NAME

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    llm_provider = LLMProvider()

    yaml_sources = []
    for path, folders, files in os.walk(source_path):
        for file in files:
            if file.endswith('.yml'):
                yaml_sources.append(os.path.join(path, file))

    # получение source_document_id из базы по названию источника
    stmt = select(SourceDocument.id).where(SourceDocument.name.match(source_name))
    source_document_id = session.execute(stmt).fetchone()[0]

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ],
        strip_headers=False,
    )

    chunk_number, page_number = 1, 1

    for i, source in enumerate(yaml_sources):
        with open(source, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)

        markdown_txt = _yaml_to_markdown(yaml_content)
        docs = splitter.split_text(markdown_txt)

        for doc in docs:
            print('Обработка чанка', chunk_number)
            embedding = llm_provider.vectorize(doc.page_content)

            try:
                new_chunk = KnowledgeBaseChunk(
                    content=doc.page_content,
                    content_type='text',
                    content_name=None,
                    embedding=embedding,
                    page_number=page_number,
                    chunk_number=chunk_number,
                    chapter_title=AVIAN_CONTENTS[i],
                    source_document_id=source_document_id
                )
                session.add(new_chunk)
            except Exception as e:
                print(f"[ERROR] Не удалось обработать страницу: {e}")
                session.rollback()
                continue

            chunk_number += 1
            if chunk_number % 5 == 0:
                page_number += 1

    try:
        session.commit()
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()


def process_swine():
    source_path, source_name = SWINE_PATH, SWINE_DOCUMENT_NAME

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    llm_provider = LLMProvider()
    json_sources = []
    for path, folders, files in os.walk(source_path):
        for file in files:
            if file.endswith('.json'):
                json_sources.append(os.path.join(path, file))

    # получение source_document_id из базы по названию источника
    stmt = select(SourceDocument.id).where(SourceDocument.name.match(source_name))
    source_document_id = session.execute(stmt).fetchone()[0]

    page_number, page_number_prev, chunk_number = 0, 0, 1
    for source in json_sources:
        chapter_title = source.split('\\')[-1].split('.')[0]

        with open(source, "r", encoding='utf-8') as f:
            data = json.load(f)

        pages = data['pages']

        splitter = BookSplitter(
            pages=pages,
            table_description_regex='^Таблица \d{1,3}',
            image_description_regex='^Рисунок \d{1,3}',
        )

        texts, tables, images = (splitter
                                 .extract_table()
                                 .extract_image()
                                 .extract_text()
                                 .after_combine_single_table_separated_by_diff_pages()
                                 .after_combine_single_text_separated_by_diff_pages()
                                 .after_split_text_chunks()
                                 .after_get_chunks())

        for chunk in [*texts, *tables, *images]:
            try:
                print('Обработка чанка', chunk_number)
                embedding = llm_provider.vectorize(chunk['content'])

                if chunk['page_number'] != page_number_prev and chunk['type'] == 'text':
                    page_number += 1
                    page_number_prev = chunk['page_number']

                new_chunk = KnowledgeBaseChunk(
                    content=chunk['content'],
                    content_type=chunk['type'],
                    content_name=chunk.get('name', None),
                    embedding=embedding,
                    page_number=page_number,
                    chunk_number=chunk_number,
                    chapter_title=chapter_title,
                    source_document_id=source_document_id
                )
                session.add(new_chunk)
                chunk_number += 1
            except Exception as e:
                print(f"[ERROR] Не удалось обработать страницу: {e}")
                session.rollback()
                continue

    try:
        session.commit()
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
