"""add drugs_chunks from galen registry with embeddings

Revision ID: 25ded9e1c150
Revises: f3a1b2c4d5e6
Create Date: 2026-03-30 20:14:42.222741

"""
import os

from alembic import op
from app.db.migrations.raw_sql_loader import load_raw_sql


# revision identifiers, used by Alembic.
revision = '25ded9e1c150'
down_revision = 'f3a1b2c4d5e6'
branch_labels = None
depends_on = None

SOURCE_FILE = 'registry_pharm_2026_03_26.xls'

DUMP_PARTS = 6


def upgrade():
    """Загрузка чанков из реестра Гален"""
    dumps_dir = os.path.join('database_data', 'dumps', revision)

    for i in range(1, DUMP_PARTS + 1):
        dump_file = os.path.join(dumps_dir, f'drugs_chunks_galen_{i}.sql')
        if os.path.exists(dump_file):
            load_raw_sql(op, dump_file)
            print(f"Loaded {dump_file}")
        else:
            print(f"Warning: {dump_file} does not exist")

    op.execute(
        "SELECT setval(pg_get_serial_sequence('drugs_chunks', 'id'), "
        "(SELECT MAX(id) FROM drugs_chunks));"
    )


def downgrade():
    """Откат: удаление чанков из реестра Гален"""
    op.execute(
        f"DELETE FROM drugs_chunks WHERE source_file = '{SOURCE_FILE}';"
    )
    op.execute(
        "SELECT setval(pg_get_serial_sequence('drugs_chunks', 'id'), "
        "COALESCE((SELECT MAX(id) FROM drugs_chunks), 1));"
    )
