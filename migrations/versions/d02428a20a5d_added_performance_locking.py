"""added performance locking

Revision ID: d02428a20a5d
Revises: c9c085ac7898
Create Date: 2017-08-17 11:09:53.689109

"""

# revision identifiers, used by Alembic.
revision = 'd02428a20a5d'
down_revision = 'c9c085ac7898'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'performances', sa.Column('in_transcription', sa.BOOLEAN()))
	op.add_column(u'performances', sa.Column('locked', sa.BOOLEAN()))

	op.execute("update performances set locked = false")
	op.execute("update performances set in_transcription = false")
	
	op.alter_column(u'performances', 'in_transcription', nullable=False)
	op.alter_column(u'performances', 'locked', nullable=False)


def downgrade():
	op.drop_column(u'performances', 'locked')
	op.drop_column(u'performances', 'in_transcription')

