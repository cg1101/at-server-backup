"""added audio upload storage

Revision ID: ed4ac60bc3fb
Revises: 029af03754fa
Create Date: 2017-03-29 16:11:02.409599

"""

# revision identifiers, used by Alembic.
revision = 'ed4ac60bc3fb'
down_revision = '029af03754fa'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'tasks', sa.Column('audio_uploads', postgresql.JSONB(), nullable=True))


def downgrade():
	op.drop_column(u'tasks', 'audio_uploads')
