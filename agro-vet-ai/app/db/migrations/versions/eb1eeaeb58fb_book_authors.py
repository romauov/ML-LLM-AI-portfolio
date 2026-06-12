"""book authors

Revision ID: eb1eeaeb58fb
Revises: 134e9d0285dc
Create Date: 2025-12-19 16:32:13.971663

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'eb1eeaeb58fb'
down_revision = '134e9d0285dc'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE source_document
        SET name = CASE id
            WHEN 1 THEN 'Болезни свиней, Зигмунд Пейсак'
            WHEN 3 THEN 'Биология и патология сельскохозяйственной птицы, Кочиш И. И.'
            WHEN 13 THEN 'Diseases of Poultry, David E. Swayne'
            WHEN 16 THEN 'Патоморфология стрептококкоза свиней в группах доращивания и откорма, Устенко Ж. Ю.'
            WHEN 17 THEN 'Патологоанатомическая диагностика болезней свиней групп доращиванния и откорма, Балабанова В. И., Кудряшев А. А.'
            WHEN 18 THEN 'Свиноматки. Практическое руководство по менеджменту лактационного периода и продуктивности свиноматок, Маррит ван Энен, Кейс Шеепенс'
            ELSE name
        END
        WHERE id IN (1, 3, 13, 16, 17, 18)
        """
    )


def downgrade():
    op.execute(
        """
        UPDATE source_document
        SET name = CASE id
            WHEN 1 THEN 'Болезни свиней'
            WHEN 3 THEN 'Биология и патология сельскохозяйственной птицы'
            WHEN 13 THEN 'Diseases of Poultry'
            WHEN 16 THEN 'Патоморфология стрептококкоза свиней в группах доращивания и откорма'
            WHEN 17 THEN 'Патологоанатомическая диагностика болезней свиней групп доращиванния и откорма'
            WHEN 18 THEN 'Свиноматки. Практическое руководство по менеджменту лактационного периода и продуктивности свиноматок'
            ELSE name
        END
        WHERE id IN (1, 3, 13, 16, 17, 18)
        """
    )
