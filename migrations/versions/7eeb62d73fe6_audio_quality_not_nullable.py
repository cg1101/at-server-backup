"""audio quality not nullable

Revision ID: 7eeb62d73fe6
Revises: 43396d8ae515
Create Date: 2017-03-31 16:45:08.998260

"""

# revision identifiers, used by Alembic.
revision = '7eeb62d73fe6'
down_revision = '43396d8ae515'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column(u'recording_platforms', 'audio_quality',
               existing_type=postgresql.JSONB(),
               nullable=False)


def downgrade():
    op.alter_column(u'recording_platforms', 'audio_quality',
               existing_type=postgresql.JSONB(),
               nullable=True)
