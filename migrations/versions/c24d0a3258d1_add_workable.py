"""add workable

Revision ID: c24d0a3258d1
Revises: f3efacc10c70
Create Date: 2017-08-30 15:57:38.557886

"""

# revision identifiers, used by Alembic.
revision = 'c24d0a3258d1'
down_revision = 'f3efacc10c70'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'worktypes', sa.Column('workable', sa.BOOLEAN(), nullable=True))
	op.execute("update worktypes set workable = true")
	op.alter_column("worktypes", "workable", nullable=False)


def downgrade():
	op.drop_column(u'worktypes', 'workable')
