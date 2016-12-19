"""added utterances

Revision ID: a0b8134317e7
Revises: bd34fc776c57
Create Date: 2016-12-19 16:27:22.413174

"""

# revision identifiers, used by Alembic.
revision = 'a0b8134317e7'
down_revision = 'bd34fc776c57'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.create_table('utterances',
	sa.Column('rawpieceid', sa.INTEGER(), nullable=False),
	sa.Column('data', postgresql.JSONB(), nullable=True),
	sa.ForeignKeyConstraint(['rawpieceid'], ['rawpieces.rawpieceid'], ),
	sa.PrimaryKeyConstraint('rawpieceid')
	)


def downgrade():
	op.drop_table('utterances')
