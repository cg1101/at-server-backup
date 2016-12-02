"""added recording feedback

Revision ID: d3d6b7e437a8
Revises: 98f4dd685611
Create Date: 2016-12-01 16:53:19.134339

"""

# revision identifiers, used by Alembic.
revision = 'd3d6b7e437a8'
down_revision = '98f4dd685611'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():

	# recording feedback
	op.create_table('recording_feedback',
	sa.Column('recording_feedback_entry_id', sa.INTEGER(), nullable=False),
	sa.Column('recording_id', sa.INTEGER(), nullable=False),
	sa.Column('userid', sa.INTEGER(), nullable=False),
	sa.Column('change_method_id', sa.INTEGER(), nullable=False),
	sa.Column('comment', sa.TEXT(), nullable=True),
	sa.Column('saved_at', postgresql.TIMESTAMP(), server_default=sa.text(u'now()'), nullable=False),
	sa.ForeignKeyConstraint(['change_method_id'], ['audio_checking_change_methods.change_method_id'], ),
	sa.ForeignKeyConstraint(['recording_id'], ['recordings.recording_id'], ),
	sa.ForeignKeyConstraint(['userid'], ['users.userid'], ),
	sa.PrimaryKeyConstraint('recording_feedback_entry_id')
	)
	op.create_index('recording_feedback_by_recording_id', 'recording_feedback', ['recording_id'], unique=False)
	
	# recording feedback flags
	op.create_table('recording_feedback_flags',
	sa.Column('recording_feedback_entry_id', sa.INTEGER(), nullable=False),
	sa.Column('recording_flag_id', sa.INTEGER(), nullable=False),
	sa.ForeignKeyConstraint(['recording_feedback_entry_id'], ['recording_feedback.recording_feedback_entry_id'], ondelete='CASCADE'),
	sa.ForeignKeyConstraint(['recording_flag_id'], ['recording_flags.recording_flag_id'], ),
	sa.PrimaryKeyConstraint('recording_feedback_entry_id', 'recording_flag_id')
	)
	op.create_index('recording_feedback_flags_by_recording_feedback_entry_id', 'recording_feedback_flags', ['recording_feedback_entry_id'], unique=False)


def downgrade():
	op.drop_index('recording_feedback_flags_by_recording_feedback_entry_id', table_name='recording_feedback_flags')
	op.drop_table('recording_feedback_flags')
	op.drop_index('recording_feedback_by_recording_id', table_name='recording_feedback')
	op.drop_table('recording_feedback')
