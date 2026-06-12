"""
Скрипт для загрузки чанков из CSV в таблицу drugs_chunks.

Заменяет все существующие данные в таблице новыми из instructions_chunks.csv
"""

import csv
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.db import build_db_url
from app.db.sqlalchemy_models import DrugChunk
from app.utils.logger import get_logger


logger = get_logger(__name__)


def load_chunks_from_csv(csv_path: str | Path = 'instructions_chunks.csv'):
    """
    Загрузка чанков из CSV в таблицу drugs_chunks.

    Args:
        csv_path: Путь к CSV файлу с чанками
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        logger.error(f'CSV файл не найден: {csv_path.absolute()}')
        sys.exit(1)

    logger.info("=" * 80)
    logger.info("ЗАГРУЗКА ЧАНКОВ В ТАБЛИЦУ drugs_chunks")
    logger.info("=" * 80)

    # 1. Подключение к БД
    logger.info("\n1. Подключение к базе данных...")
    db_url = build_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info("   ✓ Подключено")

    # 2. Удаление старых чанков
    logger.info("\n2. Удаление старых чанков...")
    old_count = session.query(DrugChunk).count()
    logger.info(f"   Старых чанков в таблице: {old_count}")

    if old_count > 0:
        session.query(DrugChunk).delete()
        session.commit()
        logger.info(f"   ✓ Удалено {old_count} чанков")

    # 3. Чтение CSV
    logger.info(f"\n3. Чтение CSV файла: {csv_path.name}...")
    chunks_data = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            chunks_data.append(row)

    logger.info(f"   ✓ Прочитано {len(chunks_data)} чанков")

    # 4. Вставка новых чанков
    logger.info("\n4. Вставка новых чанков...")
    inserted_count = 0

    for idx, row in enumerate(chunks_data, 1):
        trade_name = row['trade_name']

        # Парсим target_animals
        target_animals_str = row.get('target_animals', '')
        target_animals = [a.strip() for a in target_animals_str.split(',')] if target_animals_str else None

        # Создаем чанк
        chunk = DrugChunk(
            content=row['content'],
            section_type=row['section_type'],
            section_title=row.get('section_title') or None,
            trade_name=trade_name,
            generic_name=row.get('generic_name') or None,
            drug_class=row.get('drug_class') or None,
            dosage_form=row.get('dosage_form') or None,
            route=row.get('route') or None,
            manufacturer=row.get('manufacturer') or None,
            target_animals=target_animals,
            source_file=row.get('source_file') or None,
            source_url=row.get('source_url') or None,
            embedding=None  # Будет добавлено позже скриптом векторизации
        )

        session.add(chunk)
        inserted_count += 1

        # Коммит батчами по 50
        if inserted_count % 50 == 0:
            session.commit()
            logger.info(f"   ...inserted {inserted_count}/{len(chunks_data)} chunks")

    # Финальный коммит
    session.commit()
    logger.info(f"   Inserted {inserted_count} chunks")

    # 5. Финальная статистика
    logger.info("\n" + "=" * 80)
    logger.info("LOAD COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total chunks in CSV: {len(chunks_data)}")
    logger.info(f"Inserted to DB: {inserted_count}")

    session.close()
