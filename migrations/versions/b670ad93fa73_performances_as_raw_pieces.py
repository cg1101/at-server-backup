"""performances as raw pieces

Revision ID: b670ad93fa73
Revises: 739d94824adf
Create Date: 2016-11-24 09:57:22.440794

"""

# revision identifiers, used by Alembic.
revision = 'b670ad93fa73'
down_revision = '739d94824adf'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():

	# remove performance id columns
	op.drop_column(u'performance_meta_values', 'performance_id')
	op.drop_column(u'recordings', 'performance_id')
	op.drop_column(u'performances', 'performance_id')

	# add raw piece id column to performances
	op.execute('ALTER TABLE performances ADD COLUMN rawpieceid INTEGER PRIMARY KEY')
	op.create_foreign_key('performances_rawpieceid_fkey', 'performances', 'rawpieces', ['rawpieceid'], ['rawpieceid'])

	# add raw piece id to performance meta values
	op.add_column(u'performance_meta_values', sa.Column('rawpieceid', sa.INTEGER(), nullable=False))
	op.create_index('performance_meta_values_by_rawpieceid', 'performance_meta_values', ['rawpieceid'], unique=False)
	op.create_unique_constraint(
		'performance_meta_values_performance_meta_category_id_rawpieceid_key',
		'performance_meta_values',
		['performance_meta_category_id', 'rawpieceid']
	)
	op.create_foreign_key('performance_meta_values_rawpieceid_fkey', 'performance_meta_values', 'performances', ['rawpieceid'], ['rawpieceid'])

	# add raw piece id to recordings
	op.add_column(u'recordings', sa.Column('rawpieceid', sa.INTEGER(), nullable=False))
	op.create_index('recordings_by_rawpieceid', 'recordings', ['rawpieceid'], unique=False)
	op.create_foreign_key('recordings_rawpieceid_fkey', 'recordings', 'performances', ['rawpieceid'], ['rawpieceid'])
	
	# update raw pieces
	op.add_column(u'rawpieces', sa.Column('type', sa.TEXT(), nullable=True))
	op.alter_column(u'rawpieces', 'loadid', nullable=True)
	op.alter_column(u'rawpieces', 'rawtext', nullable=True)
	

def downgrade():

	# update raw pieces
	op.alter_column(u'rawpieces', 'rawtext', nullable=False)
	op.alter_column(u'rawpieces', 'loadid', nullable=False)
	op.drop_column(u'rawpieces', 'type')

	# remove raw piece id columns
	op.drop_column(u'performance_meta_values', 'rawpieceid')
	op.drop_column(u'recordings', 'rawpieceid')
	op.drop_column(u'performances', 'rawpieceid')

	# add performance id column to performances
	op.execute("ALTER TABLE performances ADD COLUMN performance_id SERIAL PRIMARY KEY")

	# add performance id column to performance meta values
	op.add_column(u'performance_meta_values', sa.Column('performance_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'performance_meta_values_performance_id_fkey', 'performance_meta_values', 'performances', ['performance_id'], ['performance_id'])
	op.create_unique_constraint(u'performance_meta_values_performance_meta_category_id_perfor_key', 'performance_meta_values', ['performance_meta_category_id', 'performance_id'])
	op.create_index('performance_meta_values_by_performance_id', 'performance_meta_values', ['performance_id'], unique=False)
	
	# add performance id column to recordings
	op.add_column(u'recordings', sa.Column('performance_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(u'recordings_performance_id_fkey', 'recordings', 'performances', ['performance_id'], ['performance_id'])
	op.create_index('recordings_by_performance_id', 'recordings', ['performance_id'], unique=False)
