"""added api access pairs

Revision ID: 497be45164f1
Revises: f14a373d7472
Create Date: 2017-05-18 14:53:29.971048

"""

# revision identifiers, used by Alembic.
revision = '497be45164f1'
down_revision = 'f14a373d7472'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.create_table('api_access_pairs',
	sa.Column('api_access_pair_id', sa.Integer(), nullable=False),
	sa.Column('key', sa.String(length=30), nullable=False),
	sa.Column('secret', sa.String(length=30), nullable=False),
	sa.Column('description', sa.Text(), nullable=False),
	sa.Column('userid', sa.INTEGER(), nullable=True),
	sa.Column('enabled', sa.BOOLEAN(), nullable=False),
	sa.Column('created_at', sa.DateTime(), server_default=sa.text(u'now()'), nullable=False),
	sa.ForeignKeyConstraint(['userid'], ['users.userid'], ),
	sa.PrimaryKeyConstraint('api_access_pair_id'),
	sa.UniqueConstraint('key', 'secret')
	)


def downgrade():
	op.drop_table('api_access_pairs')
