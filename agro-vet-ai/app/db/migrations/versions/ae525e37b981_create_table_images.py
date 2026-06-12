"""Create table images

Revision ID: ae525e37b981
Revises: 7252ec4b2c3e
Create Date: 2025-08-18 15:19:38.996647

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae525e37b981'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    # Создание таблицы images для хранения картинок в base64
    op.create_table(
        'images',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('chunk_id', sa.Integer, nullable=False),
        sa.Column('source_document', sa.Text, nullable=True),
        sa.Column('image_data', sa.LargeBinary, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Добавление внешнего ключа для chunk_id
    op.create_foreign_key(
        'fk_images_chunk_id_knowledge_base_chunks',
        'images',
        'knowledge_base_chunks',
        ['chunk_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Добавление комментария к таблице
    op.execute("COMMENT ON TABLE images IS 'Таблица для хранения картинок в формате base64';")


def downgrade():
    # Удаление внешнего ключа
    op.drop_constraint(
        'fk_images_chunk_id_knowledge_base_chunks',
        'images',
        type_='foreignkey'
    )

    # Удаление таблицы images
    op.drop_table('images')
