"""anemia and drugs used in treatment book

Revision ID: b98e3293817c
Revises: 52c70b7f0243
Create Date: 2025-12-05 09:39:13.506079

"""
import os

from alembic import op

from app.db.migrations.raw_sql_loader import load_raw_sql

# revision identifiers, used by Alembic.
revision = 'b98e3293817c'
down_revision = '52c70b7f0243'
branch_labels = None
depends_on = None


def upgrade():
    # Load schema and data from all SQL dump files
    migrations_dir = 'database_data'
    dumps_dir = os.path.join(migrations_dir, "dumps", revision)

    all_dump_files = [
        'source_document_15.sql',
        'knowledge_base_chunks_15.sql',
    ]

    for dump_file in all_dump_files:
        file_path = os.path.join(dumps_dir, dump_file)

        if os.path.exists(file_path):
            load_raw_sql(op, file_path)
            print(f"Loaded {dump_file}")
        else:
            print(f"Warning: {file_path} does not exist")

    op.execute("SELECT setval(pg_get_serial_sequence('source_document', 'id'), (SELECT MAX(id) FROM source_document));")
    op.execute("SELECT setval(pg_get_serial_sequence('knowledge_base_chunks', 'id'), (SELECT MAX(id) FROM knowledge_base_chunks));")


def downgrade():
    op.execute("DELETE FROM source_document WHERE name = 'Анемия и препараты, применяемые при ее лечении и профилактике';")
