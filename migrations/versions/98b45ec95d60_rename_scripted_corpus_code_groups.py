"""rename scripted corpus code groups

Revision ID: 98b45ec95d60
Revises: e5edc71852ad
Create Date: 2016-10-26 09:44:35.783968

"""

# revision identifiers, used by Alembic.
revision = '98b45ec95d60'
down_revision = 'e5edc71852ad'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():

	# drop references to scripted groups
	op.drop_index('corpus_codes_by_scripted_corpus_code_group_id', table_name='corpus_codes')
	op.drop_column(u'corpus_codes', 'scripted_corpus_code_group_id')

	# drop scripted groups
	op.drop_table('scripted_corpus_code_groups')

	# add checking groups
	op.create_table('audio_checking_groups',
	sa.Column('audio_checking_group_id', sa.INTEGER(), nullable=False),
	sa.Column('recording_platform_id', sa.INTEGER(), nullable=False),
	sa.Column('name', sa.TEXT(), nullable=False),
	sa.Column('selection_size', sa.INTEGER(), nullable=False),
	sa.CheckConstraint(u'selection_size > 0'),
	sa.ForeignKeyConstraint(['recording_platform_id'], ['recording_platforms.recording_platform_id'], ),
	sa.PrimaryKeyConstraint('audio_checking_group_id')
	)
	op.create_index('audio_checking_groups_by_recording_platform_id', 'audio_checking_groups', ['recording_platform_id'], unique=False)

	# add references to checking groups	
	op.add_column(u'corpus_codes', sa.Column('audio_checking_group_id', sa.INTEGER(), nullable=True))
	op.create_index('corpus_codes_by_audio_checking_group_id', 'corpus_codes', ['audio_checking_group_id'], unique=False)
	op.create_foreign_key(None, 'corpus_codes', 'audio_checking_groups', ['audio_checking_group_id'], ['audio_checking_group_id'])


def downgrade():

	# drop references to checking groups
	op.drop_index('corpus_codes_by_audio_checking_group_id', table_name='corpus_codes')
	op.drop_column(u'corpus_codes', 'audio_checking_group_id')

	# drop checking groups
	op.drop_table('audio_checking_groups')

	# add scripted groups
	op.create_table('scripted_corpus_code_groups',
	sa.Column('scripted_corpus_code_group_id', sa.INTEGER(), nullable=False),
	sa.Column('recording_platform_id', sa.INTEGER(), autoincrement=False, nullable=False),
	sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
	sa.Column('selection_size', sa.INTEGER(), autoincrement=False, nullable=False),
	sa.ForeignKeyConstraint(['recording_platform_id'], [u'recording_platforms.recording_platform_id'], name=u'scripted_corpus_code_groups_recording_platform_id_fkey'),
	sa.PrimaryKeyConstraint('scripted_corpus_code_group_id', name=u'scripted_corpus_code_groups_pkey')
	)
	op.create_index('corpus_codes_by_scripted_corpus_code_group_id', 'corpus_codes', ['scripted_corpus_code_group_id'], unique=False)

	# add references to scripted groups
	op.add_column(u'corpus_codes', sa.Column('scripted_corpus_code_group_id', sa.INTEGER(), autoincrement=False, nullable=True))
	op.create_index('corpus_codes_by_scripted_corpus_code_group_id', 'corpus_codes', ['scripted_corpus_code_group_id'], unique=False)
