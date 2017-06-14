"""added batch progress

Revision ID: 808403cc111d
Revises: 922592ec6793
Create Date: 2017-06-13 15:08:53.452472

"""

# revision identifiers, used by Alembic.
revision = '808403cc111d'
down_revision = '922592ec6793'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'batches', sa.Column('progress', postgresql.JSONB(), nullable=True))


def downgrade():
	op.drop_column(u'batches', 'progress')
