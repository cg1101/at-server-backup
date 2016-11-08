"""add recording flags

Revision ID: 64a4bc576418
Revises: 98b45ec95d60
Create Date: 2016-11-08 13:21:25.625243

"""

# revision identifiers, used by Alembic.
revision = '64a4bc576418'
down_revision = '98b45ec95d60'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('audio_collection_recording_flags',
    sa.Column('recording_flag_id', sa.INTEGER(), nullable=False),
    sa.Column('audio_collection_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('severity', sa.TEXT(), nullable=False),
    sa.Column('enabled', sa.BOOLEAN(), server_default='true', nullable=False),
    sa.CheckConstraint(u"severity IN ('Info', 'Warning', 'Severe')"),
    sa.ForeignKeyConstraint(['audio_collection_id'], ['audio_collections.audio_collection_id'], ),
    sa.PrimaryKeyConstraint('recording_flag_id')
    )
    op.create_index('audio_collection_recording_flags_by_audio_collection_id', 'audio_collection_recording_flags', ['audio_collection_id'], unique=False)

def downgrade():
    op.drop_index('audio_collection_recording_flags_by_audio_collection_id', table_name='audio_collection_recording_flags')
    op.drop_table('audio_collection_recording_flags')
