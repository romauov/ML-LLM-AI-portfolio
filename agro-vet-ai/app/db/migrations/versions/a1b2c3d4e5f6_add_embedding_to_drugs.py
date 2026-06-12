"""add embedding to drugs table

Revision ID: a1b2c3d4e5f6
Revises: ae525e37b981
Create Date: 2025-10-10 01:57:26.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = 'a1b2c3d4e5f6'
down_revision = '7252ec4b2c3e'
branch_labels = None
depends_on = None


def upgrade():
    # Включаем расширение pgvector (идемпотентно)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column('drugs',
        sa.Column('embedding', Vector(1536), nullable=True)
    )


def downgrade():
    op.drop_column('drugs', 'embedding')
