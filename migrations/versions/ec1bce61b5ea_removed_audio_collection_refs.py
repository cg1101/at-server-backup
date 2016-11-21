"""removed audio collection refs

Revision ID: ec1bce61b5ea
Revises: 63c26c9899ef
Create Date: 2016-11-21 17:09:42.788196

"""

# revision identifiers, used by Alembic.
revision = 'ec1bce61b5ea'
down_revision = '63c26c9899ef'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():

	# remove unused tables
	op.drop_table('audio_collection_supervisors')
	op.drop_table('audio_collection_status_log')
	
	# album meta categories
	op.drop_column(u'album_meta_categories', 'audio_collection_id')
	op.add_column(u'album_meta_categories', sa.Column('task_id', sa.INTEGER(), nullable=False))
	op.create_index('album_meta_categories_by_task_id', 'album_meta_categories', ['task_id'], unique=False)
	op.create_unique_constraint('album_meta_categories_task_id_name_key', 'album_meta_categories', ['task_id', 'name'])
	op.create_foreign_key('album_meta_categories_task_id_fkey', 'album_meta_categories', 'tasks', ['task_id'], ['taskid'])

	# albums
	op.drop_column(u'albums', 'audio_collection_id')
	op.add_column(u'albums', sa.Column('task_id', sa.INTEGER(), nullable=False))
	op.create_index('albums_by_task_id', 'albums', ['task_id'], unique=False)
	op.create_foreign_key('albums_task_id_fkey', 'albums', 'tasks', ['task_id'], ['taskid'])
	
	# meta data change log
	op.drop_column(u'meta_data_change_log', 'audio_collection_id')
	op.add_column(u'meta_data_change_log', sa.Column('task_id', sa.INTEGER(), nullable=False))
	op.create_index('meta_data_change_log_by_task_id', 'meta_data_change_log', ['task_id'], unique=False)
	op.create_foreign_key('meta_data_change_log_task_id_fkey', 'meta_data_change_log', 'tasks', ['task_id'], ['taskid'])

	# meta data change requests
	op.drop_column(u'meta_data_change_requests', 'audio_collection_id')
	op.add_column(u'meta_data_change_requests', sa.Column('task_id', sa.INTEGER(), nullable=False))
	op.create_index('meta_data_change_requests_by_task_id', 'meta_data_change_requests', ['task_id'], unique=False)
	op.create_foreign_key('meta_data_change_requests_task_id_fkey', 'meta_data_change_requests', 'tasks', ['task_id'], ['taskid'])

	# performance flags
	op.drop_column(u'performance_flags', 'audio_collection_id')
	op.add_column(u'performance_flags', sa.Column('task_id', sa.INTEGER(), nullable=False))
	op.create_index('performance_flags_by_task_id', 'performance_flags', ['task_id'], unique=False)
	op.create_unique_constraint('performance_flags_task_id_name_key', 'performance_flags', ['task_id', 'name'])
	op.create_foreign_key('performance_flags_task_id_fkey', 'performance_flags', 'tasks', ['task_id'], ['taskid'])

	# recording flags
	op.drop_column(u'recording_flags', 'audio_collection_id')
	op.add_column(u'recording_flags', sa.Column('task_id', sa.INTEGER(), nullable=False))
	op.create_index('recording_flags_by_task_id', 'recording_flags', ['task_id'], unique=False)
	op.create_unique_constraint('recording_flags_task_id_name_key', 'recording_flags', ['task_id', 'name'])
	op.create_foreign_key('recording_flags_task_id_fkey', 'recording_flags', 'tasks', ['task_id'], ['taskid'])

	# recording platforms
	op.drop_column(u'recording_platforms', 'audio_collection_id')
	op.add_column(u'recording_platforms', sa.Column('task_id', sa.INTEGER(), nullable=False))
	op.create_index('recording_platforms_by_task_id', 'recording_platforms', ['task_id'], unique=False)
	op.create_foreign_key('recording_platforms_task_id_fkey', 'recording_platforms', 'tasks', ['task_id'], ['taskid'])

	# speaker meta categories
	op.drop_column(u'speaker_meta_categories', 'audio_collection_id')
	op.add_column(u'speaker_meta_categories', sa.Column('task_id', sa.INTEGER(), nullable=False))
	op.create_index('speaker_meta_categories_by_task_id', 'speaker_meta_categories', ['task_id'], unique=False)
	op.create_unique_constraint('speaker_meta_categories_task_id_name_key', 'speaker_meta_categories', ['task_id', 'name'])
	op.create_foreign_key('speaker_meta_categories_task_id_fkey', 'speaker_meta_categories', 'tasks', ['task_id'], ['taskid'])

	# speakers
	op.drop_column(u'speakers', 'audio_collection_id')
	op.add_column(u'speakers', sa.Column('task_id', sa.INTEGER(), nullable=False))
	op.create_index('speakers_by_task_id', 'speakers', ['task_id'], unique=False)
	op.create_unique_constraint('speakers_task_id_identifier_key', 'speakers', ['task_id', 'identifier'])
	op.create_foreign_key('speakers_task_id_fkey', 'speakers', 'tasks', ['task_id'], ['taskid'])


def downgrade():
	
	# speakers
	op.drop_column(u'speakers', 'task_id')
	op.add_column(u'speakers', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'speakers_audio_collection_id_fkey', 'speakers', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('speakers_by_audio_collection_id', 'speakers', ['audio_collection_id'], unique=False)
	op.create_unique_constraint(u'speakers_audio_collection_id_identifier_key', 'speakers', ['audio_collection_id', 'identifier'])
	
	# speaker meta categories
	op.drop_column(u'speaker_meta_categories', 'task_id')
	op.add_column(u'speaker_meta_categories', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'speaker_meta_categories_audio_collection_id_fkey', 'speaker_meta_categories', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('speaker_meta_categories_by_audio_collection_id', 'speaker_meta_categories', ['audio_collection_id'], unique=False)
	op.create_unique_constraint(u'speaker_meta_categories_audio_collection_id_name_key', 'speaker_meta_categories', ['audio_collection_id', 'name'])
	
	# recording platforms
	op.drop_column(u'recording_platforms', 'task_id')
	op.add_column(u'recording_platforms', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'recording_platforms_audio_collection_id_fkey', 'recording_platforms', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('recording_platforms_by_audio_collection_id', 'recording_platforms', ['audio_collection_id'], unique=False)

	# recording flags
	op.drop_column(u'recording_flags', 'task_id')
	op.add_column(u'recording_flags', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'recording_flags_audio_collection_id_fkey', 'recording_flags', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('recording_flags_by_audio_collection_id', 'recording_flags', ['audio_collection_id'], unique=False)
	op.create_unique_constraint(u'recording_flags_audio_collection_id_name_key', 'recording_flags', ['audio_collection_id', 'name'])

	# performance flags
	op.drop_column(u'performance_flags', 'task_id')
	op.add_column(u'performance_flags', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'performance_flags_audio_collection_id_fkey', 'performance_flags', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('performance_flags_by_audio_collection_id', 'performance_flags', ['audio_collection_id'], unique=False)
	op.create_unique_constraint(u'performance_flags_audio_collection_id_name_key', 'performance_flags', ['audio_collection_id', 'name'])

	# meta data change requests
	op.drop_column(u'meta_data_change_requests', 'task_id')
	op.add_column(u'meta_data_change_requests', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'meta_data_change_requests_audio_collection_id_fkey', 'meta_data_change_requests', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('meta_data_change_requests_by_audio_collection_id', 'meta_data_change_requests', ['audio_collection_id'], unique=False)

	# meta data change log
	op.drop_column(u'meta_data_change_log', 'task_id')
	op.add_column(u'meta_data_change_log', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'meta_data_change_log_audio_collection_id_fkey', 'meta_data_change_log', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('meta_data_change_log_by_audio_collection_id', 'meta_data_change_log', ['audio_collection_id'], unique=False)

	# albums
	op.drop_column(u'albums', 'task_id')
	op.add_column(u'albums', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'albums_audio_collection_id_fkey', 'albums', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('albums_by_audio_collection_id', 'albums', ['audio_collection_id'], unique=False)

	# album meta categories
	op.drop_column(u'album_meta_categories', 'task_id')
	op.add_column(u'album_meta_categories', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'album_meta_categories_audio_collection_id_fkey', 'album_meta_categories', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
	op.create_index('album_meta_categories_by_audio_collection_id', 'album_meta_categories', ['audio_collection_id'], unique=False)
	op.create_unique_constraint(u'album_meta_categories_audio_collection_id_name_key', 'album_meta_categories', ['audio_collection_id', 'name'])


	# add audio collection status log
	op.create_table('audio_collection_status_log',
	sa.Column('log_entry_id', sa.INTEGER(), nullable=False),
	sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False),
	sa.Column('from_audio_collection_status_id', sa.INTEGER(), autoincrement=False, nullable=False),
	sa.Column('to_audio_collection_status_id', sa.INTEGER(), autoincrement=False, nullable=False),
	sa.Column('changed_by', sa.INTEGER(), autoincrement=False, nullable=False),
	sa.Column('changed_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
	sa.ForeignKeyConstraint(['audio_collection_id'], [u'audio_collections.audio_collection_id'], name=u'audio_collection_status_log_audio_collection_id_fkey'),
	sa.ForeignKeyConstraint(['changed_by'], [u'users.userid'], name=u'audio_collection_status_log_changed_by_fkey'),
	sa.ForeignKeyConstraint(['from_audio_collection_status_id'], [u'audio_collection_statuses.audio_collection_status_id'], name=u'audio_collection_status_log_from_audio_collection_status_i_fkey'),
	sa.ForeignKeyConstraint(['to_audio_collection_status_id'], [u'audio_collection_statuses.audio_collection_status_id'], name=u'audio_collection_status_log_to_audio_collection_status_id_fkey'),
	sa.PrimaryKeyConstraint('log_entry_id', name=u'audio_collection_status_log_pkey')
	)

	# add audio collection supervisors
	op.create_table('audio_collection_supervisors',
	sa.Column('audio_collection_id', sa.INTEGER(), nullable=False),
	sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
	sa.PrimaryKeyConstraint('audio_collection_id', 'user_id', name=u'audio_collection_supervisors_pkey')
	)
