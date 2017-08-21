"""modified in_transcription storage

Revision ID: f3efacc10c70
Revises: d02428a20a5d
Create Date: 2017-08-21 11:20:58.955308

"""

# revision identifiers, used by Alembic.
revision = 'f3efacc10c70'
down_revision = 'd02428a20a5d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.drop_column("performances", "in_transcription")
	op.add_column(u'performances', sa.Column('in_transcription', postgresql.JSONB(), nullable=True))


def downgrade():
	op.drop_column("performances", "in_transcription")
	op.add_column(u'performances', sa.Column('in_transcription', sa.BOOLEAN()))
	op.execute("update performances set in_transcription = false")
	op.alter_column("performances", "in_transcription", nullable=False)
