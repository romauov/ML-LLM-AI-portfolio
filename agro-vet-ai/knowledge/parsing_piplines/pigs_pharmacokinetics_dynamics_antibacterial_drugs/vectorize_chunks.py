import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import KnowledgeBaseChunk
from app.llm.providers.llm_provider import LLMProvider
from knowledge.parsing_piplines.pigs_pharmacokinetics_dynamics_antibacterial_drugs.md_chunk_splitter import MDSplitter
from knowledge.parsing_piplines.pigs_pharmacokinetics_dynamics_antibacterial_drugs.constants import JSON_BOOK, \
    SOURCE_DOCUMENT, CHAPTERS, EXCLUDED_PAGES


def get_chapter(page_number):
    for (start, end), value in CHAPTERS.items():
        if start <= page_number < end:
            return value


def process_chunks():
    """
    Основная функция для обработки текстовых фрагментов, их векторизации
    и сохранения в базу данных.
    """

    db_url = build_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    llm_provider = LLMProvider()
    with open(JSON_BOOK, "r") as f:
        data = json.load(f)

    page_data_text, page_data_tables, page_data_images = [], [], []
    splitter = MDSplitter()

    for page in data['pages']:
        page_number = page.get('index') + 1
        if page_number in EXCLUDED_PAGES:
            print(f"- Пропуск страницы {page_number} (исключена).")
            continue

        page_number = int(page_number)
        content = page.get('markdown')
        if not content.strip():
            continue

        chapter_title = get_chapter(page_number)
        text_chunks, figure_chunks, table_chunks = splitter.split(content)

        for text_chunk in text_chunks:
            if len(text_chunk.metadata) == 1 and len(page_data_text) > 0:
                last_chunk = page_data_text.pop(-1)
                last_chunk['content'] = f'{last_chunk["content"]} {text_chunk.page_content}'
                page_data_text.append(last_chunk)
            else:
                page_data_text.append({
                    'content': text_chunk.page_content,
                    'page_number': page_number,
                    'chapter_title': chapter_title,
                    'metadata': text_chunk.metadata
                })

        for table_chunk in table_chunks:
            if not table_chunk.metadata.get('name') and len(page_data_tables):
                last_chunk = page_data_tables.pop(-1)
                last_chunk['content'] = f'{last_chunk["content"]}\n{table_chunk.page_content}'
                page_data_tables.append(last_chunk)
            else:
                page_data_tables.append({
                    'content': table_chunk.page_content,
                    'page_number': page_number,
                    'chapter_title': chapter_title,
                    'metadata': table_chunk.metadata,
                })

        for figure_chunk in figure_chunks:
            page_data_images.append({
                'content': figure_chunk.page_content,
                'page_number': page_number,
                'chapter_title': chapter_title,
                'metadata': figure_chunk.metadata,
            })
    page_data = [*page_data_text, *page_data_tables, *page_data_images]
    page_data.sort(key=lambda x: x['page_number'])
    page_data = splitter.split_text_chunks(page_data)

    for chunk_number, chunk in enumerate(page_data, start=1):
        try:
            embedding = llm_provider.vectorize(chunk['content'])
            new_chunk = KnowledgeBaseChunk(
                content=chunk['content'],
                content_type=chunk['metadata']['type'],
                content_name=chunk['metadata'].get('name', None),
                embedding=embedding,
                page_number=chunk['page_number'],
                chunk_number=chunk_number,
                chapter_title=chunk['chapter_title'],
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
