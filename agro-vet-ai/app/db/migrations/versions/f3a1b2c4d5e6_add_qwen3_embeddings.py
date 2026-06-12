"""add qwen3 embedding columns to knowledge_base_chunks and drugs_chunks

Revision ID: f3a1b2c4d5e6
Revises: 31294b2a1174
Create Date: 2026-03-26 00:00:00.000000

"""
import os

from alembic import op
from app.db.migrations.raw_sql_loader import load_raw_sql

# revision identifiers, used by Alembic.
revision = 'f3a1b2c4d5e6'
down_revision = '31294b2a1174'
branch_labels = None
depends_on = None

COLUMN = 'embedding_qwen3_embedding_4b'
DIM = 2560


def upgrade():
    op.execute(f"ALTER TABLE knowledge_base_chunks ADD COLUMN IF NOT EXISTS {COLUMN} vector({DIM})")
    op.execute(f"ALTER TABLE drugs_chunks ADD COLUMN IF NOT EXISTS {COLUMN} vector({DIM})")

    dumps_dir = os.path.join('database_data', 'dumps', revision)

    for table, filename in [
        ('knowledge_base_chunks', 'knowledge_base_chunks_qwen3.sql'),
        ('drugs_chunks', 'drugs_chunks_qwen3.sql'),
    ]:
        file_path = os.path.join(dumps_dir, filename)
        if os.path.exists(file_path):
            load_raw_sql(op, file_path)
            print(f"Loaded {filename}")
        else:
            print(f"Warning: {file_path} does not exist")


def downgrade():
    op.drop_column('drugs_chunks', COLUMN)
    op.drop_column('knowledge_base_chunks', COLUMN)
