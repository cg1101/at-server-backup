"""added transitions

Revision ID: 739d94824adf
Revises: ad237d80941c
Create Date: 2016-11-23 17:37:58.511617

"""

# revision identifiers, used by Alembic.
revision = '739d94824adf'
down_revision = 'ad237d80941c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.create_table('transitions',
	sa.Column('transition_id', sa.INTEGER(), nullable=False),
	sa.Column('task_id', sa.INTEGER(), nullable=False),
	sa.Column('source_id', sa.INTEGER(), nullable=False),
	sa.Column('destination_id', sa.INTEGER(), nullable=False),
	sa.ForeignKeyConstraint(['destination_id'], ['subtasks.subtaskid'], ),
	sa.ForeignKeyConstraint(['source_id'], ['subtasks.subtaskid'], ),
	sa.ForeignKeyConstraint(['task_id'], ['tasks.taskid'], ),
	sa.PrimaryKeyConstraint('transition_id'),
	sa.UniqueConstraint('source_id', 'destination_id')
	)
	op.create_index('transitions_by_task_id', 'transitions', ['task_id'], unique=False)


def downgrade():
	op.drop_index('transitions_by_task_id', table_name='transitions')
	op.drop_table('transitions')
