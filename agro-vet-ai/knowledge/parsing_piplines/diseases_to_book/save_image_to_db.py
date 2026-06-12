import os.path

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import Images, KnowledgeBaseChunk, SourceDocument
from knowledge.parsing_piplines.diseases_to_book.constants import SWINE_DOCUMENT_NAME, SWINE_IMAGES_PATH


def save_swine_images():
    save(SWINE_DOCUMENT_NAME, SWINE_IMAGES_PATH)


def save(document_name, images_path):
    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    stmt = select(SourceDocument.id).where(SourceDocument.name.match(document_name))
    source_document_id_ = session.execute(stmt).fetchone()[0]

    stmt = select(KnowledgeBaseChunk.id).where(and_(
        KnowledgeBaseChunk.source_document_id == source_document_id_,
        KnowledgeBaseChunk.content_type.match('figure')
    )).order_by(KnowledgeBaseChunk.id.asc())
    figure_ids = [row[0] for row in session.execute(stmt).fetchall()]

    images = []
    for path, _, files in os.walk(images_path):
        for file in files:
            if file.endswith('.jpeg'):
                images.append(os.path.join(path, file))

    for i, image_path in enumerate(images):
        try:
            with open(os.path.join(images_path, image_path), "rb") as image_file:
                binary_image_data = image_file.read()

            image_ = Images(
                chunk_id=figure_ids[i],
                source_document=document_name,
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
