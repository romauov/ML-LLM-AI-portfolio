"""
Скрипт для векторизации контента чанков в таблице drugs_chunks.

Использует:
- LLMProvider для векторизации
- SQLAlchemy для работы с БД

Использование:
    python -m knowledge.parsing_piplines.drugs.vectorize_chunks
    python -m knowledge.parsing_piplines.drugs.vectorize_chunks --model qwen3
    python -m knowledge.parsing_piplines.drugs.vectorize_chunks --model qwen3 --max-chunks 10
"""

import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.sqlalchemy_models import DrugChunk
from app.llm.providers.llm_provider import LLMProvider
from app.utils.logger import get_logger
from app.utils.settings import secrets as s


logger = get_logger(__name__)


def vectorize_existing_chunks(
    max_chunks: int | None = None,
    batch_size: int = 20,
    provider: str = 'default',
    model: str | None = None,
    column: str = 'embedding',
    title: str | None = None,
):
    """
    Векторизация существующих чанков в таблице drugs_chunks.

    Args:
        max_chunks: Максимальное количество чанков для обработки (для тестирования)
        batch_size: Размер батча для commit
        provider:   Провайдер: 'default' (LLMProvider), 'lmstudio', 'openrouter', 'vsegpt'
        model:      Название модели (для lmstudio / openrouter / vsegpt)
        column:     Колонка в таблице для записи эмбеддинга
        title:      Значение хедера X-Title (для vsegpt)
    """
    logger.info("=" * 80)
    logger.info("НАЧАЛО ПРОЦЕССА ВЕКТОРИЗАЦИИ ЧАНКОВ ПРЕПАРАТОВ")
    logger.info(f"Провайдер: {provider}, модель: {model or 'из LLMProvider'}, колонка: {column}")
    logger.info("=" * 80)

    # 1. Настройка подключения к БД
    logger.info("\n1. Настройка подключения к базе данных...")
    db_url = (
        f"postgresql+psycopg://{s.postgres_user}:{s.postgres_password}"
        f"@localhost:{s.db_port_host}/{s.postgres_db}"
    )
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info("   ...подключение настроено.")

    # 2. Инициализация провайдера векторизации
    logger.info("\n2. Инициализация провайдера для векторизации...")
    if provider == 'default':
        llm_provider = LLMProvider()
        embed = llm_provider.vectorize
    elif provider == 'lmstudio':
        from openai import OpenAI
        client = OpenAI(base_url=s.inline_base_url, api_key='lmstudio')
        def embed(content):
            response = client.embeddings.create(model=model, input=[content])
            return response.data[0].embedding
    elif provider == 'openrouter':
        from openai import OpenAI
        client = OpenAI(base_url=s.openrouter_base_url, api_key=s.openrouter_api_key)
        def embed(content):
            response = client.embeddings.create(model=model, input=[content])
            return response.data[0].embedding
    elif provider == 'vsegpt':
        from openai import OpenAI
        default_headers = {'X-Title': title} if title else {}
        client = OpenAI(base_url=s.vsegpt_base_url, api_key=s.vsegpt_api_key, default_headers=default_headers)
        def embed(content):
            response = client.embeddings.create(model=model, input=[content])
            return response.data[0].embedding
    else:
        raise ValueError(f"Неизвестный провайдер: {provider!r}")
    logger.info("   ...провайдер инициализирован.")

    # 3. Подсчёт чанков для векторизации
    logger.info("\n3. Проверка чанков в БД...")
    total_chunks = session.query(DrugChunk).count()
    logger.info(f"   Всего чанков в таблице: {total_chunks}")

    chunks_without_embedding = session.execute(
        text(f"SELECT COUNT(*) FROM drugs_chunks WHERE {column} IS NULL")
    ).scalar()
    logger.info(f"   Чанков без эмбеддинга ({column}): {chunks_without_embedding}")

    if chunks_without_embedding == 0:
        logger.info("   Все чанки уже векторизованы!")
        session.close()
        return

    # 4. Векторизация чанков
    logger.info(f"\n4. Векторизация чанков (batch_size={batch_size})...")

    rows = session.execute(
        text(
            f"SELECT id, content, trade_name, section_type FROM drugs_chunks "
            f"WHERE {column} IS NULL ORDER BY id"
            + (f" LIMIT {max_chunks}" if max_chunks else "")
        )
    ).fetchall()

    total_to_process = len(rows)
    logger.info(f"   Будет обработано: {total_to_process} чанков")

    vectorized_count = 0
    error_count = 0

    for idx, (chunk_id, content, trade_name, section_type) in enumerate(rows, 1):
        try:
            embedding = embed(content)

            session.execute(
                text(f"UPDATE drugs_chunks SET {column} = :emb WHERE id = :id"),
                {'emb': str(embedding), 'id': chunk_id},
            )
            vectorized_count += 1

            if idx % 10 == 0:
                logger.info(
                    f"   [{idx}/{total_to_process}] "
                    f"Векторизован: {trade_name} - {section_type}"
                )

            if vectorized_count % batch_size == 0:
                session.commit()
                logger.info(f"   >> Промежуточный commit: {vectorized_count} чанков векторизовано")

        except Exception as e:
            logger.error(
                f"   [ERROR] Ошибка при векторизации чанка ID={chunk_id}, "
                f"{trade_name} - {section_type}: {e}"
            )
            error_count += 1
            session.rollback()
            continue

    # 5. Финальный commit
    logger.info("\n5. Финальное сохранение...")
    try:
        session.commit()
        logger.info("   ...финальный commit выполнен.")
    except Exception as e:
        logger.error(f"   [ERROR] Ошибка при финальном commit: {e}")
        session.rollback()

    # 6. Итоговая статистика
    logger.info("\n" + "=" * 80)
    logger.info("ИТОГОВАЯ СТАТИСТИКА:")
    logger.info("=" * 80)
    logger.info(f"   Всего чанков в БД: {total_chunks}")
    logger.info(f"   Обработано: {total_to_process}")
    logger.info(f"   Успешно векторизовано: {vectorized_count}")
    logger.info(f"   Ошибок: {error_count}")
    if total_to_process > 0:
        logger.info(f"   Процент успеха: {vectorized_count / total_to_process * 100:.1f}%")

    remaining = session.execute(
        text(f"SELECT COUNT(*) FROM drugs_chunks WHERE {column} IS NULL")
    ).scalar()
    logger.info(f"   Осталось без эмбеддинга: {remaining}")
    logger.info("=" * 80)

    session.close()
    logger.info("   ...сессия с БД закрыта.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Векторизация чанков drugs_chunks')
    parser.add_argument('--provider', default='default',
                        help='Провайдер: default | lmstudio | openrouter | vsegpt (default: default)')
    parser.add_argument('--model', default=None,
                        help='Название модели (для lmstudio / openrouter / vsegpt)')
    parser.add_argument('--column', default='embedding',
                        help='Колонка для записи эмбеддинга (default: embedding)')
    parser.add_argument('--title', default=None,
                        help='Значение хедера X-Title (для vsegpt)')
    parser.add_argument('--max-chunks', type=int, default=None)
    parser.add_argument('--batch-size', type=int, default=20)
    args = parser.parse_args()

    vectorize_existing_chunks(
        max_chunks=args.max_chunks,
        batch_size=args.batch_size,
        provider=args.provider,
        model=args.model,
        column=args.column,
        title=args.title,
    )
