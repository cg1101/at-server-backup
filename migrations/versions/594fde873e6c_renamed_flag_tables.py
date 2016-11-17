"""renamed flag tables

Revision ID: 594fde873e6c
Revises: 9f6e061de56f
Create Date: 2016-11-17 14:41:21.466534

"""

# revision identifiers, used by Alembic.
revision = '594fde873e6c'
down_revision = '9f6e061de56f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	
	op.drop_table('audio_collection_recording_flags')
	op.drop_table('audio_collection_performance_flags')
	
	op.create_table('performance_flags',
	sa.Column('performance_flag_id', sa.INTEGER(), nullable=False),
	sa.Column('audio_collection_id', sa.INTEGER(), nullable=False),
	sa.Column('name', sa.TEXT(), nullable=False),
	sa.Column('severity', sa.TEXT(), nullable=False),
	sa.Column('enabled', sa.BOOLEAN(), server_default='true', nullable=False),
	sa.CheckConstraint(u"severity IN ('Info', 'Warning', 'Severe')"),
	sa.ForeignKeyConstraint(['audio_collection_id'], ['audio_collections.audio_collection_id'], ),
	sa.PrimaryKeyConstraint('performance_flag_id'),
	sa.UniqueConstraint('audio_collection_id', 'name')
	)
	op.create_index('performance_flags_by_audio_collection_id', 'performance_flags', ['audio_collection_id'], unique=False)

	op.create_table('recording_flags',
	sa.Column('recording_flag_id', sa.INTEGER(), nullable=False),
	sa.Column('audio_collection_id', sa.INTEGER(), nullable=False),
	sa.Column('name', sa.TEXT(), nullable=False),
	sa.Column('severity', sa.TEXT(), nullable=False),
	sa.Column('enabled', sa.BOOLEAN(), server_default='true', nullable=False),
	sa.CheckConstraint(u"severity IN ('Info', 'Warning', 'Severe')"),
	sa.ForeignKeyConstraint(['audio_collection_id'], ['audio_collections.audio_collection_id'], ),
	sa.PrimaryKeyConstraint('recording_flag_id'),
	sa.UniqueConstraint('audio_collection_id', 'name')
	)
	op.create_index('recording_flags_by_audio_collection_id', 'recording_flags', ['audio_collection_id'], unique=False)


def downgrade():

	op.create_table('audio_collection_performance_flags',
	sa.Column('performance_flag_id', sa.INTEGER(), nullable=False),
	sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False),
	sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
	sa.Column('severity', sa.TEXT(), autoincrement=False, nullable=False),
	sa.Column('enabled', sa.BOOLEAN(), server_default=sa.text(u'true'), autoincrement=False, nullable=False),
	sa.ForeignKeyConstraint(['audio_collection_id'], [u'audio_collections.audio_collection_id'], name=u'audio_collection_performance_flags_audio_collection_id_fkey'),
	sa.PrimaryKeyConstraint('performance_flag_id', name=u'audio_collection_performance_flags_pkey')
	)

	op.create_table('audio_collection_recording_flags',
	sa.Column('recording_flag_id', sa.INTEGER(), nullable=False),
	sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False),
	sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
	sa.Column('severity', sa.TEXT(), autoincrement=False, nullable=False),
	sa.Column('enabled', sa.BOOLEAN(), server_default=sa.text(u'true'), autoincrement=False, nullable=False),
	sa.ForeignKeyConstraint(['audio_collection_id'], [u'audio_collections.audio_collection_id'], name=u'audio_collection_recording_flags_audio_collection_id_fkey'),
	sa.PrimaryKeyConstraint('recording_flag_id', name=u'audio_collection_recording_flags_pkey')
	)
	
	op.drop_table('performance_flags')
	op.drop_table('recording_flags')
