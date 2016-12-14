"""added audio quality

Revision ID: 70e27418d33e
Revises: 2daf1f8a80ae
Create Date: 2016-12-14 14:22:50.644060

"""

# revision identifiers, used by Alembic.
revision = '70e27418d33e'
down_revision = '2daf1f8a80ae'
branch_labels = None
depends_on = None

import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'recording_platforms', sa.Column('audio_quality', postgresql.JSONB(), nullable=True))

	# set default audio quality
	audio_quality = {"name": "Standard Quality", "format": "ogg", "quality": 3}
	op.execute("""
		UPDATE recording_platforms
		SET audio_quality = '{0}'
	""".format(json.dumps(audio_quality)))

def downgrade():
	op.drop_column(u'recording_platforms', 'audio_quality')

