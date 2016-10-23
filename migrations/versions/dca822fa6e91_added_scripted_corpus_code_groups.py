"""added scripted corpus code groups

Revision ID: dca822fa6e91
Revises: f25f34116907
Create Date: 2016-10-23 15:14:41.624912

"""

# revision identifiers, used by Alembic.
revision = 'dca822fa6e91'
down_revision = 'f25f34116907'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():

    op.create_table('scripted_corpus_code_groups',
    sa.Column('scripted_corpus_code_group_id', sa.INTEGER(), nullable=False),
    sa.Column('recording_platform_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('selection_size', sa.INTEGER(), nullable=False),
    sa.CheckConstraint(u'selection_size > 0'),
    sa.ForeignKeyConstraint(['recording_platform_id'], ['recording_platforms.recording_platform_id'], ),
    sa.PrimaryKeyConstraint('scripted_corpus_code_group_id')
    )
    op.create_index('scripted_corpus_code_groups_by_recording_platform_id', 'scripted_corpus_code_groups', ['recording_platform_id'], unique=False)
    op.add_column(u'corpus_codes', sa.Column('scripted_corpus_code_group_id', sa.INTEGER(), nullable=True))
    op.create_index('corpus_codes_by_scripted_corpus_code_group_id', 'corpus_codes', ['scripted_corpus_code_group_id'], unique=False)


def downgrade():
    op.drop_index('corpus_codes_by_scripted_corpus_code_group_id', table_name='corpus_codes')
    op.drop_column(u'corpus_codes', 'scripted_corpus_code_group_id')
    op.drop_index('scripted_corpus_code_groups_by_recording_platform_id', table_name='scripted_corpus_code_groups')
    op.drop_table('scripted_corpus_code_groups')
