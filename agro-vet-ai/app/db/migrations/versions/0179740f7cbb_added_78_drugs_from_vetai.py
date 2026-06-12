"""added_78_drugs_from_VetAI

Revision ID: 0179740f7cbb
Revises: efd87708ebd7
Create Date: 2025-12-05 18:40:51.461272

"""
import os
from alembic import op
from app.db.migrations.raw_sql_loader import load_raw_sql


# revision identifiers, used by Alembic.
revision = '0179740f7cbb'
down_revision = 'efd87708ebd7'
branch_labels = None
depends_on = None


def upgrade():
    """Загрузка 78 новых препаратов из VetAI в таблицу drugs"""

    migrations_dir = 'database_data'
    dumps_dir = os.path.join(migrations_dir, "dumps", revision)

    # Список файлов дампов для загрузки
    dump_files = [
        'drugs_89_to_166.sql',
    ]

    # Загрузка каждого дампа
    for dump_file in dump_files:
        file_path = os.path.join(dumps_dir, dump_file)

        if os.path.exists(file_path):
            load_raw_sql(op, file_path)
            print(f"Loaded {dump_file}")
        else:
            print(f"Warning: {file_path} does not exist")

    # Обновление последовательности ID для таблицы drugs
    op.execute(
        "SELECT setval(pg_get_serial_sequence('drugs', 'id'), "
        "(SELECT MAX(id) FROM drugs));"
    )

    print("Successfully loaded additional 78 drugs from VetAI")


def downgrade():
    """Откат: удаление 78 препаратов из VetAI"""
    op.execute("DELETE FROM drugs WHERE id BETWEEN 89 AND 166;")
    print("Rolled back: removed 78 drugs from VetAI (ID: 89-166)")