import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import Images
from knowledge.utils.common import natural_sort_key
from knowledge.parsing_piplines.practical_guide_to_broiler_health_management.constants import PARSED_DOCUMENTS_PATH, \
    SOURCE_DOCUMENT


def save():
    print("Начало процесса векторизации")
    print("Настройка подключения к базе данных")
    db_url = build_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Подключение настроено")

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
            SELECT
                id
            FROM public.knowledge_base_chunks
            WHERE content_type = 'figure'
                AND source_document_id = {source_document_id_}
            ORDER BY id ASC
        """)
        rows = conn.execute(sql_request).fetchall()

    images = []
    for dir_ in sorted(os.listdir(PARSED_DOCUMENTS_PATH), key=natural_sort_key):
        path = os.path.join(PARSED_DOCUMENTS_PATH, dir_, 'images')
        if os.path.exists(path):
            for image_name in sorted(os.listdir(path), key=natural_sort_key):
                images.append(os.path.join(path, image_name))

    for i, image in enumerate(images):
        with open(image, "rb") as image_file:
            binary_image_data = image_file.read()

        image_ = Images(
            chunk_id=rows[i].id,
            source_document=SOURCE_DOCUMENT,
            image_data=binary_image_data
        )
        session.add(image_)

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
