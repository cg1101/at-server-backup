"""rename importers to loaders

Revision ID: 029af03754fa
Revises: 1fbb7a87c4f3
Create Date: 2017-03-27 10:55:16.839801

"""

# revision identifiers, used by Alembic.
revision = '029af03754fa'
down_revision = '1fbb7a87c4f3'
branch_labels = None
depends_on = None

import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from migrations.seed import add_seed_data


def upgrade():

	# update loaders with audio checking features
	op.add_column(u'loaders', sa.Column('all_performances_incomplete', sa.BOOLEAN(), nullable=True))
	op.add_column(u'loaders', sa.Column('metadata_sources', postgresql.JSONB(), nullable=True))

	# add audio checking loaders
	add_seed_data("loaders", {
		"name" : "Unstructured",
		"all_performances_incomplete": True
	})
	add_seed_data("loaders", {
		"name" : "Standard",
		"all_performances_incomplete": False
	})
	add_seed_data("loaders", {
		"name" : "Appen Mobile Recorder - Scripted",
		"all_performances_incomplete": False,
		"metadata_sources": json.dumps(["Log File"]),
	})
	add_seed_data("loaders", {
		"name" : "Appen Mobile Recorder - Conversational",
		"all_performances_incomplete": False
	})
	add_seed_data("loaders", {
		"name" : "Appen Telephony - Scripted",
		"all_performances_incomplete": False
	})
	add_seed_data("loaders", {
		"name" : "Appen Telephony - Conversational",
		"all_performances_incomplete": False,
		"metadata_sources": json.dumps(["Log File"]),
	})
	
	# rename performances imported at column
	op.alter_column(u'performances', 'imported_at', new_column_name='loaded_at')


	# update recording platforms
	
	# add reference to loaders
	op.add_column(u'recording_platforms', sa.Column('loader_id', sa.INTEGER(), nullable=True))
	op.create_foreign_key('recording_platforms_loader_id_fkey', 'recording_platforms', 'loaders', ['loader_id'], ['loader_id'])
	
	# update loader references
	conn = op.get_bind()
	result = conn.execute("""
		select recording_platform_id, audio_importers.name
		from
			recording_platforms join
			audio_importers using (audio_importer_id)
	""").fetchall()

	for recording_platform_id, loader_name in result:
		conn.execute("""
			update recording_platforms
			set loader_id = (
				select loader_id
				from loaders
				where name = '{0}'
			)
			where recording_platform_id = {1}
		""".format(loader_name, recording_platform_id))

	# remove reference to audio importers
	op.drop_column(u'recording_platforms', 'audio_importer_id')
	

	# remove audio importers
	op.drop_table('audio_importers')


def downgrade():

	# create audio importers table
	op.create_table('audio_importers',
		sa.Column('audio_importer_id', sa.INTEGER(), nullable=False),
		sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
		sa.Column('all_performances_incomplete', sa.BOOLEAN(), server_default=sa.text(u'false'), autoincrement=False, nullable=False),
		sa.Column('metadata_sources', postgresql.JSONB(), autoincrement=False, nullable=True),
		sa.PrimaryKeyConstraint('audio_importer_id', name=u'audio_importers_pkey'),
		sa.UniqueConstraint('name', name=u'audio_importers_name_key')
	)

	# add audio importers
	add_seed_data("loaders", {
		"name" : "Unstructured",
		"all_performances_incomplete": True
	})
	add_seed_data("loaders", {
		"name" : "Standard",
		"all_performances_incomplete": False
	})
	add_seed_data("loaders", {
		"name" : "Appen Mobile Recorder - Scripted",
		"all_performances_incomplete": False,
		"metadata_sources": json.dumps(["Log File"]),
	})
	add_seed_data("loaders", {
		"name" : "Appen Mobile Recorder - Conversational",
		"all_performances_incomplete": False
	})
	add_seed_data("loaders", {
		"name" : "Appen Telephony - Scripted",
		"all_performances_incomplete": False
	})
	add_seed_data("loaders", {
		"name" : "Appen Telephony - Conversational",
		"all_performances_incomplete": False,
		"metadata_sources": json.dumps(["Log File"]),
	})


	# update recording platforms

	# add reference to audio importers
	op.add_column(u'recording_platforms', sa.Column('audio_importer_id', sa.INTEGER(), autoincrement=False, nullable=True))
	op.create_foreign_key(u'recording_platforms_audio_importer_id_fkey', 'recording_platforms', 'audio_importers', ['audio_importer_id'], ['audio_importer_id'])
	
	# update importer references
	conn = op.get_bind()
	result = conn.execute("""
		select recording_platform_id, loaders.name
		from
			recording_platforms join
			loaders using (loader_id)
	""").fetchall()

	for recording_platform_id, loader_name in result:
		conn.execute("""
			update recording_platforms
			set audio_importer_id = (
				select audio_importer_id
				from audio_importers
				where name = '{0}'
			)
			where recording_platform_id = {1}
		""".format(loader_name, recording_platform_id))
	
	# remove reference to loaders
	op.drop_column(u'recording_platforms', 'loader_id')
	

	# rename performances imported at column
	op.alter_column(u'performances', 'loaded_at', new_column_name='imported_at')

	# remove audio checking features
	op.drop_column(u'loaders', 'metadata_sources')
	op.drop_column(u'loaders', 'all_performances_incomplete')
	

