import os.path

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import Images, KnowledgeBaseChunk, SourceDocument
from knowledge.parsing_piplines.antimicrobial_prescribing_guidelines_for_pigs.constants import SOURCE_DOCUMENT, \
    IMAGES_PATH
from knowledge.utils.common import natural_sort_key


def save():
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

    try:
        session.commit()
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
