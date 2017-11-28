"""added auto loading flag

Revision ID: dd6f561ad861
Revises: 130090387260
Create Date: 2017-11-28 17:23:26.107737

"""

# revision identifiers, used by Alembic.
revision = 'dd6f561ad861'
down_revision = '130090387260'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'tasks', sa.Column('auto_loading', sa.BOOLEAN(), nullable=True))


def downgrade():
	op.drop_column(u'tasks', 'auto_loading')
