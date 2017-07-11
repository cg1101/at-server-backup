"""added new change method

Revision ID: 6cc505c0eb62
Revises: 3026502be744
Create Date: 2017-02-27 14:25:29.713304

"""

# revision identifiers, used by Alembic.
revision = '6cc505c0eb62'
down_revision = '3026502be744'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
	pass # used to be seed data migration


def downgrade():
	pass # used to be seed data migration
