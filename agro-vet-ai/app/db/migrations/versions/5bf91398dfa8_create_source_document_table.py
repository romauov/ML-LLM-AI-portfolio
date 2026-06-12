"""create source document table

Revision ID: 5bf91398dfa8
Revises: a1b2c3d4e5f6
Create Date: 2025-11-06 09:49:19.087120

"""
from string import ascii_letters

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5bf91398dfa8'
down_revision = 'ae525e37b981'
branch_labels = None
depends_on = None


def upgrade():
    # Создание таблицы source_document
    op.create_table(
        'source_document',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.Text, nullable=True),
        sa.Column('language', sa.Text, nullable=True),
        sa.Column('contents', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.execute("COMMENT ON TABLE source_document IS 'Таблица для хранения информации об источниках';")

    # Перенос источников из knowledge_base_chunks в source_document
    conn = op.get_bind()

    documents_name = conn.execute(sa.text("SELECT DISTINCT source_document FROM knowledge_base_chunks")).fetchall()
    data = []
    for document_name in documents_name:
        name = document_name[0]
        query = sa.text(
            f"""
                SELECT string_agg(chapter_title, '\n') AS content FROM (
                    SELECT chapter_title, source_document FROM (
                        SELECT distinct on (chapter_title) chapter_title, page_number, source_document
                        FROM public.knowledge_base_chunks
                        WHERE source_document = '{name}'
                    )
                    ORDER BY page_number asc
                )
            """
        )
        document_content = conn.execute(query).fetchone()
        document_language = 'en' if document_content[0][0] in ascii_letters else 'ru'
        data.append((document_name[0], document_language, document_content[0]))

    if data:
        conn.execute(
            sa.text("""
                INSERT INTO source_document (name, language, contents)
                VALUES (:name, :language, :contents)
            """),
            [
                {"name": item[0], "language": item[1], "contents": item[2]}
                for item in data
            ]
        )

    # Замена поля knowledge_base_chunks.source_document на id из таблицы source_document
    op.add_column(
        'knowledge_base_chunks',
        sa.Column('source_document_id', sa.Integer(), nullable=True)
    )

    update_query = sa.text("""
        UPDATE public.knowledge_base_chunks
        SET source_document_id = sd.id
        FROM source_document sd
        WHERE public.knowledge_base_chunks.source_document = sd.name
    """)
    conn.execute(update_query)

    op.alter_column('knowledge_base_chunks', 'source_document_id', nullable=False)
    op.drop_column('knowledge_base_chunks', 'source_document')

    # Добавление внешнего ключа для source_document_id
    op.create_foreign_key(
        'fk_knowledge_base_chunks_source_document_id_source_document',
        'knowledge_base_chunks',
        'source_document',
        ['source_document_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Удаление внешнего ключа
    op.drop_constraint(
        'fk_knowledge_base_chunks_source_document_id_source_document',
        'knowledge_base_chunks',
        type_='foreignkey'
    )

    # Перенос источников из source_document в knowledge_base_chunks
    conn = op.get_bind()

    # Замена поля knowledge_base_chunks.source_document_id на knowledge_base_chunks.source_document
    op.add_column(
        'knowledge_base_chunks',
        sa.Column('source_document', sa.String(), nullable=True)
    )

    query = sa.text("""
       UPDATE public.knowledge_base_chunks
       SET source_document = sd.name
       FROM source_document sd
       WHERE public.knowledge_base_chunks.source_document_id = sd.id
    """)
    conn.execute(query)

    op.drop_column('knowledge_base_chunks', 'source_document_id')

    # Удаление таблицы
    op.drop_table('source_document')
