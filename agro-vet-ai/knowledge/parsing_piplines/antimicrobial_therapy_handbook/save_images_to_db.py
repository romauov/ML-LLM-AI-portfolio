import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import Images
from knowledge.utils.common import natural_sort_key

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SOURCE_DOCUMENT = "Antimicrobial Therapy in Veterinary Medicine, 5th Edition"
JSON_HANDBOOK = os.path.join(
    PROJECT_ROOT,
    'knowledge/data/antimicrobial_therapy_handbook/',
    f'{SOURCE_DOCUMENT}.json'
)
IMAGES_PATH = os.path.join('knowledge/data/antimicrobial_therapy_handbook/', 'parsed_images')


def save():
    print("1. Настройка подключения к базе данных...")

    db_url = build_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

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
            ORDER BY id asc
        """)
        rows = conn.execute(sql_request).fetchall()

    figure_ids = [r.id for r in rows]

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

    print("3. Сохранение всех изменений в базе данных...")
    try:
        session.commit()
        print("   ...изменения успешно сохранены.")
    except Exception as e:
        print(f"[ERROR] Ошибка при коммите в БД: {e}")
        session.rollback()
    finally:
        session.close()
        print("   ...сессия с БД закрыта.")
