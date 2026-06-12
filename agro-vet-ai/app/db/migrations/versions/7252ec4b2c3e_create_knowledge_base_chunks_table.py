"""create_knowledge_base_chunks_table

Revision ID: 7252ec4b2c3e
Revises: e0f94523f2b0
Create Date: 2025-08-04 11:20:42.855677

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '7252ec4b2c3e'
down_revision = 'e0f94523f2b0'
branch_labels = None
depends_on = None


def upgrade():
    # Включаем расширение pgvector (идемпотентно)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Создание таблицы knowledge_base_chunks с векторным полем embedding
    op.create_table(
        'knowledge_base_chunks',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_type', sa.Text, nullable=True),
        sa.Column('content_name', sa.Text, nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('page_number', sa.Integer, nullable=True),
        sa.Column('chunk_number', sa.Integer, nullable=True),
        sa.Column('chapter_title', sa.Text, nullable=True),
        sa.Column('keywords', ARRAY(sa.Text), nullable=True),
        sa.Column('source_document', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Добавление комментария к таблице
    op.execute("COMMENT ON TABLE knowledge_base_chunks IS 'Таблица для хранения фрагментов знаний из справочников';")


def downgrade():
    # Удаление таблицы knowledge_base_chunks
    op.drop_table('knowledge_base_chunks')
