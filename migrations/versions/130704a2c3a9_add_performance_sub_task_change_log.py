"""add performance sub task change log

Revision ID: 130704a2c3a9
Revises: 58d29f9b32ad
Create Date: 2016-12-28 22:32:02.676286

"""

# revision identifiers, used by Alembic.
revision = '130704a2c3a9'
down_revision = '58d29f9b32ad'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.create_table('performance_transition_log',
	sa.Column('log_entry_id', sa.INTEGER(), nullable=False),
	sa.Column('rawpieceid', sa.INTEGER(), nullable=False),
	sa.Column('source_id', sa.INTEGER(), nullable=False),
	sa.Column('destination_id', sa.INTEGER(), nullable=False),
	sa.Column('userid', sa.INTEGER(), nullable=True),
	sa.Column('change_method_id', sa.INTEGER(), nullable=False),
	sa.Column('moved_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
	sa.ForeignKeyConstraint(['change_method_id'], ['audio_checking_change_methods.change_method_id'], ),
	sa.ForeignKeyConstraint(['destination_id'], ['subtasks.subtaskid'], ),
	sa.ForeignKeyConstraint(['rawpieceid'], ['performances.rawpieceid'], ),
	sa.ForeignKeyConstraint(['source_id'], ['subtasks.subtaskid'], ),
	sa.ForeignKeyConstraint(['userid'], ['users.userid'], ),
	sa.PrimaryKeyConstraint('log_entry_id')
	)
	op.create_index('performance_transition_log_by_rawpieceid', 'performance_transition_log', ['rawpieceid'], unique=False)

def downgrade():
	op.drop_table('performance_transition_log')
