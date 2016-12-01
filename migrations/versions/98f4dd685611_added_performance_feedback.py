"""added performance feedback

Revision ID: 98f4dd685611
Revises: 103696ef5788
Create Date: 2016-11-30 14:49:31.218858

"""

# revision identifiers, used by Alembic.
revision = '98f4dd685611'
down_revision = '103696ef5788'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from migrations.seed import add_seed_data

def upgrade():
	
	# audio checking change methods
	op.create_table('audio_checking_change_methods',
	sa.Column('change_method_id', sa.INTEGER(), nullable=False),
	sa.Column('name', sa.TEXT(), nullable=False),
	sa.PrimaryKeyConstraint('change_method_id'),
	sa.UniqueConstraint('name')
	)
	add_seed_data("audio_checking_change_methods", {"name" : "Admin"})
	add_seed_data("audio_checking_change_methods", {"name" : "Work Page"})

	# performance feedback
	op.create_table('performance_feedback',
	sa.Column('performance_feedback_entry_id', sa.INTEGER(), nullable=False),
	sa.Column('rawpieceid', sa.INTEGER(), nullable=False),
	sa.Column('userid', sa.INTEGER(), nullable=False),
	sa.Column('change_method_id', sa.INTEGER(), nullable=False),
	sa.Column('comment', sa.TEXT(), nullable=True),
	sa.Column('saved_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
	sa.ForeignKeyConstraint(['change_method_id'], ['audio_checking_change_methods.change_method_id'], ),
	sa.ForeignKeyConstraint(['rawpieceid'], ['performances.rawpieceid'], ),
	sa.ForeignKeyConstraint(['userid'], ['users.userid'], ),
	sa.PrimaryKeyConstraint('performance_feedback_entry_id')
	)
	op.create_index('performance_feedback_by_rawpieceid', 'performance_feedback', ['rawpieceid'], unique=False)
	
	# performance feedback flags
	op.create_table('performance_feedback_flags',
	sa.Column('performance_feedback_entry_id', sa.INTEGER(), nullable=False),
	sa.Column('performance_flag_id', sa.INTEGER(), nullable=False),
	sa.ForeignKeyConstraint(['performance_feedback_entry_id'], ['performance_feedback.performance_feedback_entry_id'], ondelete="CASCADE"),
	sa.ForeignKeyConstraint(['performance_flag_id'], ['performance_flags.performance_flag_id'], ),
	sa.PrimaryKeyConstraint('performance_feedback_entry_id', 'performance_flag_id')
	)
	op.create_index('performance_feedback_flags_by_performance_feedback_entry_id', 'performance_feedback_flags', ['performance_feedback_entry_id'], unique=False)
	

def downgrade():
	op.drop_index('performance_feedback_flags_by_performance_feedback_entry_id', table_name='performance_feedback_flags')
	op.drop_table('performance_feedback_flags')
	op.drop_index('performance_feedback_by_rawpieceid', table_name='performance_feedback')
	op.drop_table('performance_feedback')
	op.drop_table('audio_checking_change_methods')
