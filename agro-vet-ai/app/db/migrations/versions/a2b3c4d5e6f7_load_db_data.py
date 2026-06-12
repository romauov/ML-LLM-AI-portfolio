"""load schema and data from dump

Revision ID: a2b3c4d5e6f7
Revises: 5bf91398dfa8
Create Date: 2025-11-24 15:10:00.000000

"""
from alembic import op
import os
from app.db.migrations.raw_sql_loader import load_raw_sql


# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = '5bf91398dfa8'
branch_labels = None
depends_on = None


def upgrade():
    # Load schema and data from all SQL dump files
    migrations_dir = 'database_data'
    dumps_dir = os.path.join(migrations_dir, "dumps", "a2b3c4d5e6f7_init")

    # Connect to the database

    # Define separate lists for different categories
    drugs_files = [
        'drugs.sql'
    ]

    source_document_files = [
        'source_document_1.sql', 'source_document_2.sql', 'source_document_3.sql',
        'source_document_4.sql', 'source_document_5.sql', 'source_document_6.sql',
        'source_document_7.sql', 'source_document_8.sql', 'source_document_9.sql'
    ]

    knowledge_base_chunks_files = [
        'knowledge_base_chunks_1.sql', 'knowledge_base_chunks_2.sql', 'knowledge_base_chunks_3.sql',
        'knowledge_base_chunks_4.sql', 'knowledge_base_chunks_5.sql', 'knowledge_base_chunks_6.sql',
        'knowledge_base_chunks_7.sql', 'knowledge_base_chunks_8.sql', 'knowledge_base_chunks_9.sql'
    ]

    image_files = [
        'images_1.sql', 'images_2.sql', 'images_3.sql',
        'images_4.sql', 'images_5.sql', 'images_6.sql',
        'images_7.sql', 'images_8.sql', 'images_9.sql'
    ]

    all_dump_files = drugs_files + source_document_files + \
        knowledge_base_chunks_files + image_files

    for dump_file in all_dump_files:
        file_path = os.path.join(dumps_dir, dump_file)

        if os.path.exists(file_path):
            load_raw_sql(op, file_path)
            print(f"Loaded {dump_file}")
        else:
            print(f"Warning: {file_path} does not exist")

    op.execute("SELECT setval(pg_get_serial_sequence('source_document', 'id'), (SELECT MAX(id) FROM source_document));")
    op.execute("SELECT setval(pg_get_serial_sequence('images', 'id'), (SELECT MAX(id) FROM images));")
    op.execute("SELECT setval(pg_get_serial_sequence('drugs', 'id'), (SELECT MAX(id) FROM drugs));")
    op.execute("SELECT setval(pg_get_serial_sequence('knowledge_base_chunks', 'id'), (SELECT MAX(id) FROM knowledge_base_chunks));")
    op.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users));")

def downgrade():
    # CASCADE автоматически очистит связанные данные в зависимых таблицах
    op.execute("TRUNCATE TABLE drugs RESTART IDENTITY CASCADE;")
    op.execute("TRUNCATE TABLE source_document RESTART IDENTITY CASCADE;")
