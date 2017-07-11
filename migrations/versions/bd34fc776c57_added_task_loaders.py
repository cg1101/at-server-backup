"""added task loaders

Revision ID: bd34fc776c57
Revises: 43ae3baf400c
Create Date: 2016-12-19 14:11:38.018790

"""

# revision identifiers, used by Alembic.
revision = 'bd34fc776c57'
down_revision = '43ae3baf400c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.create_table('loaders',
	sa.Column('loader_id', sa.INTEGER(), nullable=False),
	sa.Column('name', sa.TEXT(), nullable=False),
	sa.PrimaryKeyConstraint('loader_id'),
	sa.UniqueConstraint('name')
	)
	op.add_column(u'tasks', sa.Column('loader_id', sa.INTEGER(), nullable=True))

	
def downgrade():
	op.drop_column(u'tasks', 'loader_id')
	op.drop_table('loaders')

