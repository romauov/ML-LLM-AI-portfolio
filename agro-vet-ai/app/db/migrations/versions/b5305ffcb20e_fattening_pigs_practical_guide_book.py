"""fattening pigs practical guide book

Revision ID: b5305ffcb20e
Revises: eb1eeaeb58fb
Create Date: 2025-12-22 14:02:38.605376

"""
import os

from alembic import op

from app.db.migrations.raw_sql_loader import load_raw_sql

# revision identifiers, used by Alembic.
revision = 'b5305ffcb20e'
down_revision = 'eb1eeaeb58fb'
branch_labels = None
depends_on = None


def upgrade():
    # Load schema and data from all SQL dump files
    migrations_dir = 'database_data'
    dumps_dir = os.path.join(migrations_dir, "dumps", revision)

    all_dump_files = [
        'source_document_19.sql',
        'knowledge_base_chunks_19.sql',
        'images_19.sql',
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
    op.execute("DELETE FROM source_document WHERE name = 'Откорм свиней. Практическое руководство по росту, здоровью и поведению животных';")
