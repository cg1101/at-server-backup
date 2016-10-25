"""added audio checking sections

Revision ID: e5edc71852ad
Revises: dca822fa6e91
Create Date: 2016-10-25 09:41:29.066558

"""

# revision identifiers, used by Alembic.
revision = 'e5edc71852ad'
down_revision = 'dca822fa6e91'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.create_table('audio_checking_sections',
	sa.Column('audio_checking_section_id', sa.INTEGER(), nullable=False),
	sa.Column('recording_platform_id', sa.INTEGER(), nullable=False),
	sa.Column('start_position', postgresql.DOUBLE_PRECISION(), nullable=False),
	sa.Column('end_position', postgresql.DOUBLE_PRECISION(), nullable=False),
	sa.Column('check_percentage', postgresql.DOUBLE_PRECISION(), nullable=False),
	sa.CheckConstraint(u'check_percentage > 0 AND check_percentage <= 1'),
	sa.CheckConstraint(u'end_position > 0 AND end_position <= 1'),
	sa.CheckConstraint(u'start_position >= 0 AND start_position < 1'),
	sa.ForeignKeyConstraint(['recording_platform_id'], ['recording_platforms.recording_platform_id'], ),
	sa.PrimaryKeyConstraint('audio_checking_section_id')
	)
	op.create_index('audio_checking_sections_by_recording_platform_id', 'audio_checking_sections', ['recording_platform_id'], unique=False)

def downgrade():
	op.drop_index('audio_checking_sections_by_recording_platform_id', table_name='audio_checking_sections')
	op.drop_table('audio_checking_sections')
