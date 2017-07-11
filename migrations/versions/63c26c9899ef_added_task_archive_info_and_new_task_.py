"""added task archive info and new task types

Revision ID: 63c26c9899ef
Revises: 594fde873e6c
Create Date: 2016-11-21 16:24:11.454113

"""

# revision identifiers, used by Alembic.
revision = '63c26c9899ef'
down_revision = '594fde873e6c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'tasks', sa.Column('archive_info', postgresql.JSONB(), nullable=True))

def downgrade():
	op.drop_column(u'tasks', 'archive_info')
