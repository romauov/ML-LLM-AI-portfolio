import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import SourceDocument
from knowledge.parsing_piplines.vic_articles_swine.constants import SOURCE_DOCUMENT, JSON_ARTICLES


def add_source():
    """Добавление сущности `источник документа` в базу данных по статьям ВИК"""

    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    with open(JSON_ARTICLES, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    # В качестве содержания (contents) перечислим названия всех статей
    article_titles = [article['title'] for article in articles]

    document = SourceDocument(
        name=SOURCE_DOCUMENT,
        language='ru',
        contents='\n'.join(article_titles),
    )

    session.add(document)

    try:
        session.commit()
        print(f"Источник '{SOURCE_DOCUMENT}' успешно добавлен.")
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    add_source()
