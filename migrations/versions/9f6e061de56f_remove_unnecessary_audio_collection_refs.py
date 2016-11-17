"""remove unnecessary audio collection refs

Revision ID: 9f6e061de56f
Revises: 64a4bc576418
Create Date: 2016-11-17 11:05:52.712505

"""

# revision identifiers, used by Alembic.
revision = '9f6e061de56f'
down_revision = '64a4bc576418'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():

	# audio files
	op.drop_constraint(u'audio_files_audio_collection_id_fkey', 'audio_files', type_='foreignkey')
	op.drop_column(u'audio_files', 'audio_collection_id')
	
	# corpus codes
	op.create_index('corpus_codes_by_recording_platform_id', 'corpus_codes', ['recording_platform_id'], unique=False)
	op.create_unique_constraint(u'corpus_codes_recording_platform_id_code_key', 'corpus_codes', ['recording_platform_id', 'code'])
	op.drop_column(u'corpus_codes', 'audio_collection_id')

	# performances
	op.drop_column(u'performances', 'audio_collection_id')

	# recording meta categories
	op.create_index('recording_meta_categories_by_recording_platform_id', 'recording_meta_categories', ['recording_platform_id'], unique=False)
	op.create_unique_constraint(u'recording_meta_categories_recording_platform_id_name_key', 'recording_meta_categories', ['recording_platform_id', 'name'])
	op.drop_column(u'recording_meta_categories', 'audio_collection_id')

	# recordings
	op.create_index('recordings_by_recording_platform_id', 'recordings', ['recording_platform_id'], unique=False)
	op.drop_column(u'recordings', 'audio_collection_id')


def downgrade():

	# recordings
	op.add_column(u'recordings', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'recordings_audio_collection_id_fkey', 'recordings', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('recordings_by_audio_collection_id', 'recordings', ['audio_collection_id'], unique=False)
	op.drop_index('recordings_by_recording_platform_id', table_name='recordings')

	# recording meta categories
	op.add_column(u'recording_meta_categories', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'recording_meta_categories_audio_collection_id_fkey', 'recording_meta_categories', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.drop_constraint(u'recording_meta_categories_recording_platform_id_name_key', 'recording_meta_categories', type_='unique')
	op.create_index('recording_meta_categories_by_audio_collection_id', 'recording_meta_categories', ['audio_collection_id'], unique=False)
	op.create_unique_constraint(u'recording_meta_categories_audio_collection_id_name_key', 'recording_meta_categories', ['audio_collection_id', 'name'])
	op.drop_index('recording_meta_categories_by_recording_platform_id', table_name='recording_meta_categories')

	# performances
	op.add_column(u'performances', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'performances_audio_collection_id_fkey', 'performances', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('performances_by_audio_collection_id', 'performances', ['audio_collection_id'], unique=False)

	# corpus codes
	op.add_column(u'corpus_codes', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'corpus_codes_audio_collection_id_fkey', 'corpus_codes', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.drop_constraint('corpus_codes_recording_platform_id_code_key', 'corpus_codes', type_='unique')
	op.create_index('corpus_codes_by_audio_collection_id', 'corpus_codes', ['audio_collection_id'], unique=False)
	op.create_unique_constraint(u'corpus_codes_audio_collection_id_code_key', 'corpus_codes', ['audio_collection_id', 'code'])
	op.drop_index('corpus_codes_by_recording_platform_id', table_name='corpus_codes')

	# audio files
	op.add_column(u'audio_files', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'audio_files_audio_collection_id_fkey', 'audio_files', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
