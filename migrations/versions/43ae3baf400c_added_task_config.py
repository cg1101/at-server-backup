"""added task config

Revision ID: 43ae3baf400c
Revises: 70e27418d33e
Create Date: 2016-12-19 12:31:49.491171

"""

# revision identifiers, used by Alembic.
revision = '43ae3baf400c'
down_revision = '70e27418d33e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'tasks', sa.Column('config', postgresql.JSONB(), nullable=True))

def downgrade():
	op.drop_column(u'tasks', 'config')
