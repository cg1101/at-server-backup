"""album speaker updates

Revision ID: d01de4a07b27
Revises: a333c4b713e4
Create Date: 2017-07-19 17:23:13.510701

"""

# revision identifiers, used by Alembic.
revision = 'd01de4a07b27'
down_revision = 'a333c4b713e4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'albums', sa.Column('name', sa.TEXT(), nullable=True))
	op.create_unique_constraint(None, 'albums', ['task_id', 'name'])
	op.alter_column(u'albums', 'speaker_id', existing_type=sa.INTEGER(), nullable=True)
	op.add_column(u'performances', sa.Column('speaker_id', sa.INTEGER(), nullable=True))


def downgrade():
	op.drop_column(u'albums', 'name')
	op.alter_column(u'albums', 'speaker_id', existing_type=sa.INTEGER(), nullable=False)
	op.drop_column(u'performances', 'speaker_id')
