import os.path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import Images
from knowledge.parsing_piplines.birds_biology_and_pathology.constants import SOURCE_DOCUMENT, IMAGES_PATH
from knowledge.utils.common import natural_sort_key


def save():
    engine = create_engine(build_db_url())
    session = sessionmaker(bind=engine)()

    with engine.connect() as conn:
        sql_request = text(f"""
            SELECT id
            FROM public.source_document
            WHERE name = '{SOURCE_DOCUMENT}'
        """)
        source_document_id_ = conn.execute(sql_request).fetchone()[0]

    # получаем id чанков с изображениями по порядку
    with engine.connect() as conn:
        sql_request = text(f"""
            SELECT id
            FROM public.knowledge_base_chunks
            WHERE content_type = 'figure'
                AND source_document_id = {source_document_id_}
            ORDER BY id ASC
        """)
        rows = conn.execute(sql_request).fetchall()

    figure_ids = [r.id for r in rows]
    figure_idx = 0

    for image_path in sorted(os.listdir(IMAGES_PATH), key=natural_sort_key):
        try:
            with open(os.path.join(IMAGES_PATH, image_path), "rb") as image_file:
                binary_image_data = image_file.read()

            image_ = Images(
                chunk_id=figure_ids[figure_idx],
                source_document=SOURCE_DOCUMENT,
                image_data=binary_image_data
            )

            session.add(image_)
            figure_idx += 1
        except Exception as e:
            print(f"[ERROR] Не удалось обработать изображение: {e}")
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


if __name__ == "__main__":
    save()
