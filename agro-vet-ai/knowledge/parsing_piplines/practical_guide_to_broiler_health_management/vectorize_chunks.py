import os
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import KnowledgeBaseChunk
from app.llm.providers.llm_provider import LLMProvider
from knowledge.parsing_piplines.practical_guide_to_broiler_health_management.constants import PARSED_DOCUMENTS_PATH, \
    SOURCE_DOCUMENT
from knowledge.parsing_piplines.practical_guide_to_broiler_health_management.md_chunk_splitter import MDSplitter
from knowledge.utils.common import natural_sort_key


def process_chunks():
    """
    Основная функция для обработки текстовых фрагментов, их векторизации
    и сохранения в базу данных.
    """
    print("Начало процесса векторизации")
    print("Настройка подключения к базе данных")
    db_url = build_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Подключение настроено")

    llm_provider = LLMProvider()
    print("Начало обработки текстовых фрагментов")

    page_number = 0
    chunk_number = 0

    for dir_ in sorted(os.listdir(PARSED_DOCUMENTS_PATH), key=natural_sort_key):

        images = []
        path = os.path.join(PARSED_DOCUMENTS_PATH, dir_, 'images')
        for image_name in os.listdir(path):
            images.append(os.path.join(path, image_name))

        md_files = []
        for sub_dirs in os.listdir(os.path.join(PARSED_DOCUMENTS_PATH, dir_)):
            path = os.path.join(PARSED_DOCUMENTS_PATH, dir_, sub_dirs)
            if path.endswith('.md'):
                title = re.split(r'(/|\\)', path)[-1].split('.md')[0].replace('_', ' ').capitalize()
                md_files.append([path, title])

        for file, title in md_files:
            page_number += 1
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

            text_chunks, figure_chunks, table_chunks = MDSplitter(content).split()

            for chunk in [*text_chunks, *figure_chunks, *table_chunks]:
                content = chunk.page_content
                content_type = chunk.metadata.get('type')
                content_name = chunk.metadata.get('name')
                embedding = llm_provider.vectorize(chunk.page_content)
                chunk_number += 1

                # Создание объекта и добавление в сессию
                new_chunk = KnowledgeBaseChunk(
                    content=content,
                    content_type=content_type,
                    content_name=content_name,
                    embedding=embedding,
                    page_number=page_number,
                    chunk_number=chunk_number,
                    chapter_title=title,
                    source_document=SOURCE_DOCUMENT
                )
                session.add(new_chunk)

    print("Сохранение всех изменений в базе данных")
    try:
        session.commit()
        print("изменения успешно сохранены.")
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
        print("сессия с БД закрыта.")

    print("Процесс векторизации завершен")
