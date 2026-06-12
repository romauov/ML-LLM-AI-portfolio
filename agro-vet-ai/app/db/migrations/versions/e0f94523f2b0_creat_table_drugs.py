"""Creat table drugs

Revision ID: e0f94523f2b0
Revises: 4fa529ea220f
Create Date: 2025-01-24 19:54:37.672818

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0f94523f2b0'
down_revision = '4fa529ea220f'
branch_labels = None
depends_on = None

def upgrade():
    # Создание таблицы drugs
    op.create_table(
        'drugs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True, comment="Уникальный идентификатор препарата"),
        sa.Column('trade_name', sa.Text, nullable=False, comment="Торговое название препарата"),
        sa.Column('generic_name', sa.Text, nullable=False, comment="Международное непатентованное название (действующее вещество)"),
        sa.Column('drug_class', sa.Text, nullable=False, comment="Фармакологическая группа (например, антибиотик, анестетик)"),
        sa.Column('dosage_form', sa.Text, nullable=False, comment="Лекарственная форма (например, таблетки, инъекции)"),
        sa.Column('route', sa.Text, nullable=False, comment="Способ применения (например, наружно, внутрь)"),
        sa.Column('target_animals', sa.ARRAY(sa.Text), nullable=False, comment="Список животных, для которых препарат может применяться"),
        sa.Column('manufacturer', sa.Text, nullable=False, comment="Производитель препарата"),
        sa.Column('instruction', sa.Text, nullable=False, comment="Инструкция по применению"),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False, comment="Дата и время создания записи"),
    )

    # Добавление комментария к таблице
    op.execute("COMMENT ON TABLE drugs IS 'Таблица для хранения информации о ветеринарных препаратах';")


def downgrade():
    # Удаление таблицы drugs
    op.drop_table('drugs')
