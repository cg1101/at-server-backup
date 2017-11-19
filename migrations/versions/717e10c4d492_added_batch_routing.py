"""added batch routing

Revision ID: 717e10c4d492
Revises: f7527fcfb31e
Create Date: 2017-11-15 14:22:17.873898

"""

# revision identifiers, used by Alembic.
revision = '717e10c4d492'
down_revision = 'f7527fcfb31e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('batch_router',
    sa.Column('batch_router_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('task_id', sa.INTEGER(), nullable=False),
    sa.Column('enabled', sa.BOOLEAN(), nullable=False),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.taskid'], ),
    sa.PrimaryKeyConstraint('batch_router_id'),
    sa.UniqueConstraint('name', 'task_id')
    )
    op.create_index('batch_router_by_task_id', 'batch_router', ['task_id'], unique=False)

    op.create_table('batch_router_sub_task',
    sa.Column('batch_router_sub_task_id', sa.INTEGER(), nullable=False),
    sa.Column('batch_router_id', sa.INTEGER(), nullable=False),
    sa.Column('sub_task_id', sa.INTEGER(), nullable=False),
    sa.Column('criteria', postgresql.JSONB(), nullable=True),
    sa.ForeignKeyConstraint(['batch_router_id'], ['batch_router.batch_router_id'], ),
    sa.ForeignKeyConstraint(['sub_task_id'], ['subtasks.subtaskid'], ),
    sa.PrimaryKeyConstraint('batch_router_sub_task_id'),
    sa.UniqueConstraint('batch_router_id', 'sub_task_id')
    )
    op.create_index('batch_router_sub_task_by_batch_router_id', 'batch_router_sub_task', ['batch_router_id'], unique=False)
    op.create_index('batch_router_sub_task_by_sub_task_id', 'batch_router_sub_task', ['sub_task_id'], unique=False)


def downgrade():
    op.drop_table('batch_router_sub_task')
    op.drop_table('batch_router')
