#!/usr/bin/env python
"""
Векторизация knowledge_base_chunks и drugs_chunks

Логика:
  - Для статейных чанков (content начинается с '[Статья:') — векторизуем текст БЕЗ
    метаданных-префикса.
  - Для остальных чанков — векторизуем content as-is.
  - Колонка создаётся автоматически если её нет.
  - Чанки с уже заполненным эмбеддингом пропускаются.

Использование:
    python knowledge/utils/generate_chunk_embeddings.py
"""
import sys
import time
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from openai import OpenAI

from app.utils.settings import secrets as s

EMBED_MODEL = "qwen/qwen3-embedding-4b"
COLUMN_NAME = "embedding_qwen3_embedding_4b"
BATCH_SIZE  = 20

# добавлял в статьи метаданные, которые не должны попасть в эмбеддинг
ARTICLE_PREFIX_RE = re.compile(r"^\[Статья:.*?\]\n", re.DOTALL)


def build_db_url() -> str:
    return (
        f"postgresql+psycopg://{s.postgres_user}:{s.postgres_password}"
        f"@localhost:{s.db_port_host}/{s.postgres_db}"
    )


def strip_article_prefix(content: str) -> str:
    """Убирает '[Статья: ... ]\n' из начала чанков статей."""
    return ARTICLE_PREFIX_RE.sub("", content, count=1).strip()


def get_text_to_embed(content: str) -> str:
    """Возвращает текст для векторизации (без префикса для статей)."""
    if content.startswith("[Статья:"):
        return strip_article_prefix(content)
    return content.strip()


def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Векторизация батча через OpenRouter."""
    response = client.embeddings.create(model=EMBED_MODEL, input=texts)
    items = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in items]


def ensure_column(engine, table: str, dim: int):
    """Добавляет колонку COLUMN_NAME vector(dim) в таблицу если её нет."""
    with engine.begin() as conn:
        exists = conn.execute(text("""
            SELECT 1 FROM information_schema.columns
            WHERE table_name = :table AND column_name = :col
        """), {"table": table, "col": COLUMN_NAME}).scalar()

        if not exists:
            print(f"Добавляю колонку {COLUMN_NAME} vector({dim}) в {table}...")
            conn.execute(text(
                f"ALTER TABLE {table} ADD COLUMN {COLUMN_NAME} vector({dim})"
            ))
            print(f"Колонка создана.")
        else:
            print(f"Колонка {COLUMN_NAME} уже существует.")


def vectorize_table(client: OpenAI, engine, table: str, dim: int, get_text=None):
    """Векторизует чанки таблицы table в колонку COLUMN_NAME.

    get_text — функция преобразования content перед эмбеддингом (опционально).
    """
    if get_text is None:
        get_text = str.strip

    print(f"\n--- Таблица: {table} ---")

    ensure_column(engine, table, dim)

    with engine.connect() as conn:
        total_missing = conn.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE {COLUMN_NAME} IS NULL")
        ).scalar()

    print(f"Чанков без {COLUMN_NAME}: {total_missing}")
    if total_missing == 0:
        print("Все чанки уже векторизованы, пропускаем.")
        return

    processed = 0
    errors = 0
    start_id = 0
    start_time = time.time()

    with engine.connect() as conn:
        fetch_sql = text(f"""
            SELECT id, content
            FROM {table}
            WHERE {COLUMN_NAME} IS NULL
              AND id >= :start_id
            ORDER BY id
            LIMIT :limit
        """)

        while processed < total_missing:
            rows = conn.execute(fetch_sql, {
                "limit": BATCH_SIZE,
                "start_id": start_id,
            }).fetchall()

            if not rows:
                break

            ids   = [r.id for r in rows]
            texts = [get_text(r.content) for r in rows]

            try:
                embeddings = embed_batch(client, texts)
            except Exception as e:
                print(f"[ERROR] Батч id={ids[0]}..{ids[-1]}: {e}")
                errors += len(ids)
                processed += len(ids)
                start_id = ids[-1] + 1
                continue

            with engine.begin() as upd_conn:
                for chunk_id, emb in zip(ids, embeddings):
                    upd_conn.execute(
                        text(f"UPDATE {table} SET {COLUMN_NAME} = :emb WHERE id = :id"),
                        {"emb": str(emb), "id": chunk_id},
                    )

            processed += len(rows)
            start_id = ids[-1] + 1
            elapsed = time.time() - start_time
            speed = processed / elapsed if elapsed > 0 else 0
            remaining = (total_missing - processed) / speed if speed > 0 else 0

            print(
                f"  [{processed}/{total_missing}] "
                f"id={ids[0]}..{ids[-1]} | "
                f"{speed:.1f} чанк/с | "
                f"осталось ~{remaining/60:.1f} мин"
            )

    print(f"Готово. Обработано: {processed}, ошибок: {errors}")


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    client = OpenAI(base_url=s.openrouter_base_url, api_key=s.openrouter_api_key)
    engine = create_engine(build_db_url())

    print(f"Модель: {EMBED_MODEL}")
    test_emb = embed_batch(client, ["test"])[0]
    dim = len(test_emb)
    print(f"Размерность эмбеддинга: {dim}")

    vectorize_table(client, engine, "knowledge_base_chunks", dim, get_text=get_text_to_embed)
    vectorize_table(client, engine, "drugs_chunks", dim)


if __name__ == "__main__":
    main()
