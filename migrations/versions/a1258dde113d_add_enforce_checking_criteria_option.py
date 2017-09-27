"""add enforce checking criteria option

Revision ID: a1258dde113d
Revises: 5242730fe284
Create Date: 2017-09-27 09:11:53.079968

"""

# revision identifiers, used by Alembic.
revision = 'a1258dde113d'
down_revision = '5242730fe284'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'subtasks', sa.Column('enforce_checking_criteria', sa.BOOLEAN()))
	op.execute("update subtasks set enforce_checking_criteria = true")
	op.alter_column("subtasks", "enforce_checking_criteria", nullable=False)


def downgrade():
	op.drop_column(u'subtasks', 'enforce_checking_criteria')
