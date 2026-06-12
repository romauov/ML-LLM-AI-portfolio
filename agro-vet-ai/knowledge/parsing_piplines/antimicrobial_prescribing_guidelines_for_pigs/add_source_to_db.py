from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import SourceDocument

from knowledge.parsing_piplines.antimicrobial_prescribing_guidelines_for_pigs.constants import CHAPTERS, SOURCE_DOCUMENT


def add_source():
    """Добавление сущности `источник документа` в базу данных по книге Antimicrobial prescribing guidelines for pigs"""

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    document = SourceDocument(
        name=SOURCE_DOCUMENT,
        language='en',
        contents='\n'.join(CHAPTERS.values()),
    )

    session.add(document)

    try:
        session.commit()
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
