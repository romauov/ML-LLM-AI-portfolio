import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import SourceDocument
from knowledge.parsing_piplines.diseases_to_book.constants import SWINE_DOCUMENT_NAME, AVIAN_DOCUMENT_NAME, \
    SWINE_PATH, AVIAN_CONTENTS


def add_source():
    """Добавление сущности `источник документа` в базу данных по карточкам болезней птиц и свиней"""

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    # Свиньи
    swine_chapters = []
    for path, folders, files in os.walk(SWINE_PATH):
        for file in files:
            if file.endswith('.json'):
                swine_chapters.append(file.split('.')[0])

    document = SourceDocument(
        name=SWINE_DOCUMENT_NAME,
        language='ru',
        contents='\n'.join(swine_chapters),
    )

    session.add(document)

    # Птицы
    document = SourceDocument(
        name=AVIAN_DOCUMENT_NAME,
        language='ru',
        contents='\n'.join(AVIAN_CONTENTS),
    )

    session.add(document)

    try:
        session.commit()
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
