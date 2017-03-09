"""added task stats column

Revision ID: 7a0572fe5890
Revises: 6cc505c0eb62
Create Date: 2017-03-09 08:57:30.375165

"""

# revision identifiers, used by Alembic.
revision = '7a0572fe5890'
down_revision = '6cc505c0eb62'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'tasks', sa.Column('stats', postgresql.JSONB(), nullable=True))
	op.create_foreign_key('tasks_loader_id_fkey', 'tasks', 'loaders', ['loader_id'], ['loader_id'])


def downgrade():
	op.drop_constraint('tasks_loader_id_fkey', 'tasks', type_='foreignkey')
	op.drop_column(u'tasks', 'stats')
