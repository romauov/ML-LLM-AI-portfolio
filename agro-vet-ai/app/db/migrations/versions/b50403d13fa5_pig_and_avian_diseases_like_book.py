"""pig and avian diseases like book

Revision ID: b50403d13fa5
Revises: a2b3c4d5e6f7
Create Date: 2025-11-27 16:21:43.223045

"""
import os

from alembic import op

from app.db.migrations.raw_sql_loader import load_raw_sql

# revision identifiers, used by Alembic.
revision = 'b50403d13fa5'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    # Load schema and data from all SQL dump files
    migrations_dir = 'database_data'
    dumps_dir = os.path.join(migrations_dir, "dumps", revision)

    all_dump_files = [
        'backup_document_10.sql',
        'backup_document_11.sql',
        'backup_knowledge_base_chunks_10.sql',
        'backup_knowledge_base_chunks_11.sql',
        'backup_images_10.sql',
    ]

    for dump_file in all_dump_files:
        file_path = os.path.join(dumps_dir, dump_file)

        if os.path.exists(file_path):
            load_raw_sql(op, file_path)
            print(f"Loaded {dump_file}")
        else:
            print(f"Warning: {file_path} does not exist")

    op.execute("SELECT setval(pg_get_serial_sequence('source_document', 'id'), (SELECT MAX(id) FROM source_document));")
    op.execute("SELECT setval(pg_get_serial_sequence('images', 'id'), (SELECT MAX(id) FROM images));")
    op.execute("SELECT setval(pg_get_serial_sequence('knowledge_base_chunks', 'id'), (SELECT MAX(id) FROM knowledge_base_chunks));")


def downgrade():
    op.execute("DELETE FROM source_document WHERE name = 'Сборник: Болезни свиней';")
    op.execute("DELETE FROM source_document WHERE name = 'Сборник: Болезни птиц';")
