import os.path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.db import build_db_url
from app.db.sqlalchemy_models import Images
from knowledge.parsing_piplines.avian_pathology.constants import SOURCE_DOCUMENT, IMAGES_PATH
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

    # Проверяем наличие изображений
    if not os.path.exists(IMAGES_PATH):
        print(f"[ERROR] Папка с изображениями не найдена: {IMAGES_PATH}")
        return

    image_files = sorted(os.listdir(IMAGES_PATH), key=natural_sort_key)
    print(f"Найдено {len(image_files)} файлов изображений в {IMAGES_PATH}")

    if len(image_files) != len(figure_ids):
        print(f"[WARNING] Количество изображений ({len(image_files)}) не совпадает с количеством figure чанков ({len(figure_ids)})")

    print(f"\n{'='*80}")
    print("Обработка изображений:")
    print(f"{'='*80}\n")

    figure_idx = 0
    saved_count = 0

    for image_path in image_files:
        try:
            print(f"[{figure_idx + 1}/{len(image_files)}] Обработка: {image_path}")

            full_path = os.path.join(IMAGES_PATH, image_path)
            with open(full_path, "rb") as image_file:
                binary_image_data = image_file.read()

            image_ = Images(
                chunk_id=figure_ids[figure_idx],
                source_document=SOURCE_DOCUMENT,
                image_data=binary_image_data
            )

            session.add(image_)
            saved_count += 1
            print(f"  ✓ Добавлено в сессию (chunk_id: {figure_ids[figure_idx]})\n")
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