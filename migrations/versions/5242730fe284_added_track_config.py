"""added track config

Revision ID: 5242730fe284
Revises: f5b552012981
Create Date: 2017-09-15 13:48:47.685578

"""

# revision identifiers, used by Alembic.
revision = '5242730fe284'
down_revision = 'f5b552012981'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'tracks', sa.Column('disabled', sa.BOOLEAN(), nullable=True))
	op.add_column(u'tracks', sa.Column('muted', sa.BOOLEAN(), nullable=True))

	op.execute("update tracks set disabled = false, muted = false")

	op.alter_column("tracks", "disabled", nullable=False)
	op.alter_column("tracks", "muted", nullable=False)


def downgrade():
	op.drop_column(u'tracks', 'muted')
	op.drop_column(u'tracks', 'disabled')
