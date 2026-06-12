"""Creat table users

Revision ID: 4fa529ea220f
Revises: 6e38d4c60c3c
Create Date: 2025-01-23 19:26:23.677222

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fa529ea220f'
down_revision = '6e38d4c60c3c'
branch_labels = None
depends_on = None

def upgrade():
    # Создание таблицы users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('telegram_id', sa.BigInteger, nullable=False, unique=True),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade():
    # Удаление таблицы users
    op.drop_table('users')