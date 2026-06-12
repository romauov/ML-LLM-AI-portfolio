"""recreate_drugs_chunks_table

Revision ID: 242232e46a03
Revises: 4317265dbc91
Create Date: 2026-02-02 07:04:58.994973

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from pgvector.sqlalchemy import Vector
import os
from app.db.migrations.raw_sql_loader import load_raw_sql


# revision identifiers, used by Alembic.
revision = '242232e46a03'
down_revision = '4317265dbc91'
branch_labels = None
depends_on = None


def upgrade():
    # Включаем расширение pgvector (идемпотентно)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Создание таблицы drugs_chunks с векторным полем embedding
    op.create_table(
        'drugs_chunks',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('source_file', sa.Text, nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('generic_name', sa.Text, nullable=True),
        sa.Column('trade_name', sa.Text, nullable=False),
        sa.Column('manufacturer', sa.Text, nullable=True),
        sa.Column('dosage_form', sa.Text, nullable=True),
        sa.Column('route', sa.Text, nullable=True),
        sa.Column('drug_class', sa.Text, nullable=True),
        sa.Column('target_animals', ARRAY(sa.Text), nullable=True),
        sa.Column('section_type', sa.Text, nullable=False),
        sa.Column('section_title', sa.Text, nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('source_url', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('search_vector', TSVECTOR, nullable=True),
    )

    # Добавление комментария к таблице
    op.execute("COMMENT ON TABLE drugs_chunks IS 'Таблица для хранения чанков инструкций препаратов для RAG';")
    op.create_index('idx_drugs_chunks_trade_name', 'drugs_chunks', ['trade_name'])
    op.create_index('idx_drugs_chunks_section_type', 'drugs_chunks', ['section_type'])
    op.create_index('idx_drugs_chunks_drug_class', 'drugs_chunks', ['drug_class'])
    op.execute('CREATE INDEX idx_drugs_chunks_target_animals ON drugs_chunks USING GIN (target_animals)')
    op.execute('CREATE INDEX idx_drugs_chunks_embedding ON drugs_chunks USING hnsw (embedding vector_cosine_ops)')

    # Создание функции-триггера для автоматического обновления search_vector
    op.execute("""
        CREATE OR REPLACE FUNCTION drugs_chunks_search_vector_update()
        RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('russian', coalesce(NEW.trade_name, '')), 'A') ||
                setweight(to_tsvector('russian', coalesce(NEW.generic_name, '')), 'A') ||
                setweight(to_tsvector('russian', coalesce(NEW.drug_class, '')), 'B') ||
                setweight(to_tsvector('russian', coalesce(NEW.manufacturer, '')), 'C') ||
                setweight(to_tsvector('russian', coalesce(NEW.dosage_form, '')), 'C') ||
                setweight(to_tsvector('russian', coalesce(NEW.route, '')), 'C') ||
                setweight(to_tsvector('russian', coalesce(NEW.content, '')), 'D');
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql;
    """)

    # Создание триггера
    op.execute("""
        CREATE TRIGGER trig_drugs_chunks_search_vector_update
        BEFORE INSERT OR UPDATE ON drugs_chunks
        FOR EACH ROW EXECUTE FUNCTION drugs_chunks_search_vector_update();
    """)

    # Создание GIN индекса для search_vector
    op.execute('CREATE INDEX idx_drugs_chunks_search_vector ON drugs_chunks USING GIN (search_vector)')

    # Загрузка данных из dump-файла
    dumps_dir = os.path.join('database_data', 'dumps', '242232e46a03')
    dump_file = os.path.join(dumps_dir, 'drugs_chunks_data.sql')

    if os.path.exists(dump_file):
        load_raw_sql(op, dump_file)
        print(f"Loaded drugs_chunks_data.sql")
        # Восстанавливаем search_path после dump (он сбрасывает его на '')
        op.execute("SET search_path TO public;")
    else:
        print(f"Warning: {dump_file} does not exist")


def downgrade():
    # Удаление триггера и функции перед удалением таблицы
    op.execute("DROP TRIGGER IF EXISTS trig_drugs_chunks_search_vector_update ON drugs_chunks;")
    op.execute("DROP FUNCTION IF EXISTS drugs_chunks_search_vector_update();")
    # Удаление таблицы drugs_chunks (каскадное удаление индексов происходит автоматически)
    op.execute("DROP TABLE IF EXISTS drugs_chunks CASCADE")
