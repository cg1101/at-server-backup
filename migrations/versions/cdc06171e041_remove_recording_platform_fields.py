"""remove recording platform fields

Revision ID: cdc06171e041
Revises: ffd71a38d1a2
Create Date: 2017-06-23 17:13:53.078308

"""

# revision identifiers, used by Alembic.
revision = 'cdc06171e041'
down_revision = 'ffd71a38d1a2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.drop_column(u'recording_platforms', 'default_audio_spec')
	op.drop_column(u'recording_platforms', 'audio_cutup_config')
	op.drop_column(u'recording_platforms', 'storage_location')
	op.drop_column(u'recording_platforms', 'master_hypothesis_file')
	op.drop_column(u'recording_platforms', 'master_script_file')


def downgrade():
	op.add_column(u'recording_platforms', sa.Column('master_script_file', postgresql.JSONB(), autoincrement=False, nullable=True))
	op.add_column(u'recording_platforms', sa.Column('master_hypothesis_file', postgresql.JSONB(), autoincrement=False, nullable=True))
	op.add_column(u'recording_platforms', sa.Column('storage_location', sa.TEXT(), autoincrement=False, nullable=True))
	op.add_column(u'recording_platforms', sa.Column('audio_cutup_config', postgresql.JSONB(), autoincrement=False, nullable=True))
	op.add_column(u'recording_platforms', sa.Column('default_audio_spec', postgresql.JSONB(), autoincrement=False, nullable=True))
