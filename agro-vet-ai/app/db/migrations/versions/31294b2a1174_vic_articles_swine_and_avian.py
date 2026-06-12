"""vic articles swine and avian

Revision ID: 31294b2a1174
Revises: 242232e46a03
Create Date: 2026-02-24 16:00:00.000000

"""
import os

from alembic import op

from app.db.migrations.raw_sql_loader import load_raw_sql

# revision identifiers, used by Alembic.
revision = '31294b2a1174'
down_revision = '242232e46a03'
branch_labels = None
depends_on = None

DUMPS_DIR = os.path.join('database_data', 'dumps', revision)

DUMP_FILES = [
    'source_document_articles.sql',
    'knowledge_base_chunks_articles.sql',
    'images_articles.sql',
]


def _load_article_names() -> list[str]:
    path = os.path.join(DUMPS_DIR, 'article_names.txt')
    with open(path, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def upgrade():
    for dump_file in DUMP_FILES:
        file_path = os.path.join(DUMPS_DIR, dump_file)
        if os.path.exists(file_path):
            load_raw_sql(op, file_path)
            print(f'Loaded {dump_file}')
        else:
            print(f'Warning: {file_path} does not exist')

    op.execute("SELECT setval(pg_get_serial_sequence('source_document', 'id'), (SELECT MAX(id) FROM source_document));")
    op.execute("SELECT setval(pg_get_serial_sequence('knowledge_base_chunks', 'id'), (SELECT MAX(id) FROM knowledge_base_chunks));")
    op.execute("SELECT setval(pg_get_serial_sequence('images', 'id'), (SELECT MAX(id) FROM images));")


def downgrade():
    for name in _load_article_names():
        escaped = name.replace("'", "''")
        op.execute(f"DELETE FROM source_document WHERE name = '{escaped}';")
