"""
Скрипт для векторизации существующих записей в таблице drugs.
Объединяет все поля с метаданными в единый текст для векторизации.

Использует паттерн из:
- rag/antimicrobial_therapy_handbook/vectorize_fragments.py
- rag/practical_guide_to_broiler_health_management/vectorize_chunks.py

Запуск: python scripts/vectorize_drugs.py
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.llm.providers.llm_provider import LLMProvider
from app.db.db import build_db_url
from app.db.sqlalchemy_models import Drug
from app.utils.logger import get_logger

app_logger = get_logger(__name__)


def format_drug_for_embedding(drug: Drug) -> str:
    """
    Форматирует данные препарата в текст для векторизации.
    Добавляет метаданные к каждому полю для улучшения семантического поиска.

    Пример выхода:
    "Торговое название: Пульмосол
    Действующее вещество: Флорфеникол
    Фармакологическая группа: Антибиотик
    Лекарственная форма: Раствор для инъекций
    Способ применения: Внутримышечно
    Целевые животные: КРС, Свиньи
    Производитель: Завод #3
    Инструкция: [ТЕКСТ ИНСТРУКЦИИ]"

    Args:
        drug: Объект Drug из SQLAlchemy ORM

    Returns:
        Форматированная строка для векторизации
    """
    # Обработка массива животных
    if isinstance(drug.target_animals, list):
        animals = ', '.join(drug.target_animals)
    else:
        animals = str(drug.target_animals)

    # Собираем все поля с метаданными
    parts = [
        f"Торговое название: {drug.trade_name}",
        f"Действующее вещество: {drug.generic_name}",
        f"Фармакологическая группа: {drug.drug_class}",
        f"Лекарственная форма: {drug.dosage_form}",
        f"Способ применения: {drug.route}",
        f"Целевые животные: {animals}",
        f"Производитель: {drug.manufacturer}",
        f"Инструкция: {drug.instruction}"
    ]

    return "\n".join(parts)


def vectorize_all_drugs():
    """
    Векторизация всех препаратов в БД.
    Использует паттерн из vectorize_fragments.py с SQLAlchemy ORM.
    """
    app_logger.info("--- Начало процесса векторизации препаратов ---")

    # 1. Настройка подключения к БД
    app_logger.info("1. Настройка подключения к базе данных...")
    db_url = build_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    app_logger.info("   ...подключение настроено.")

    # 2. Инициализация VseGPT провайдера
    app_logger.info("2. Инициализация VseGPT провайдера для векторизации...")
    llm_provider = LLMProvider()
    app_logger.info("   ...провайдер инициализирован.")

    # 3. Получаем все препараты без эмбеддинга
    app_logger.info("3. Загрузка препаратов для векторизации...")
    drugs = session.query(Drug).filter(Drug.embedding.is_(None)).all()
    total_drugs = len(drugs)
    app_logger.info(f"   Найдено {total_drugs} препаратов для векторизации")

    if total_drugs == 0:
        app_logger.info("   Все препараты уже векторизованы!")
        session.close()
        return

    # 4. Векторизация каждого препарата
    app_logger.info("4. Начало векторизации препаратов...")
    success_count = 0
    error_count = 0

    for i, drug in enumerate(drugs, 1):
        try:
            text_for_embedding = format_drug_for_embedding(drug)
            embedding = llm_provider.vectorize(text_for_embedding)

            # ВАЖНО: SQLAlchemy автоматически конвертирует list[float] в pgvector
            drug.embedding = embedding
            app_logger.info(f"   [{i}/{total_drugs}] Векторизован препарат ID={drug.id}: {drug.trade_name}")
            success_count += 1

            # Commit через каждые 10 препаратов
            if i % 10 == 0:
                session.commit()
                app_logger.info(f"   >> Промежуточный commit: {i} препаратов обработано")

        except Exception as e:
            app_logger.error(
                f"   [ERROR] Ошибка при векторизации препарата ID={drug.id} "
                f"({drug.trade_name}): {e}"
            )
            error_count += 1
            session.rollback()
            continue

    # 5. Финальный commit
    app_logger.info("5. Сохранение всех изменений в базе данных...")
    try:
        session.commit()
        app_logger.info(
            f"   ✅ Успешно векторизовано: {success_count} препаратов"
        )
        if error_count > 0:
            app_logger.warning(f"   ⚠️  Ошибок при векторизации: {error_count}")
        app_logger.info("   ...изменения успешно сохранены.")
    except Exception as e:
        app_logger.error(f"   [ERROR] Ошибка при финальном commit: {e}")
        session.rollback()
    finally:
        session.close()
        app_logger.info("   ...сессия с БД закрыта.")

    app_logger.info("--- Процесс векторизации завершен ---")


if __name__ == "__main__":
    vectorize_all_drugs()
