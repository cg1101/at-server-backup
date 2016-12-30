"""audio checking change method for meta data changes

Revision ID: 0de4dea9470c
Revises: 130704a2c3a9
Create Date: 2016-12-29 15:22:49.523004

"""

# revision identifiers, used by Alembic.
revision = '0de4dea9470c'
down_revision = '130704a2c3a9'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	
	# remove meta data change methods
	op.drop_column(u'meta_data_change_log', 'meta_data_change_method_id')
	op.drop_column(u'meta_data_change_requests', 'meta_data_change_method_id')
	op.drop_table('meta_data_change_methods')

	# add fk for meta data change log user
	op.create_foreign_key(
		u'meta_data_change_log_changed_by_fkey',
		'meta_data_change_log',
		'users',
		['changed_by'],
		['userid']
	)

	# add references to audio checking change methods
	op.add_column(u'meta_data_change_log', sa.Column('change_method_id', sa.INTEGER(), nullable=False))
	op.create_foreign_key(
		u'meta_data_change_log_change_method_id_fkey',
		'meta_data_change_log',
		'audio_checking_change_methods',
		['change_method_id'],
		['change_method_id']
	)
	op.add_column(u'meta_data_change_requests', sa.Column('change_method_id', sa.INTEGER(), nullable=False))
	op.create_foreign_key(
		u'meta_data_change_log_change_method_id_fkey',
		'meta_data_change_requests',
		'audio_checking_change_methods',
		['change_method_id'],
		['change_method_id']
	)


def downgrade():
	
	# remove references to audio checking change methods
	op.drop_column(u'meta_data_change_requests', 'change_method_id')
	op.drop_column(u'meta_data_change_log', 'change_method_id')

	# add fk for meta data change log user
	op.drop_constraint('meta_data_change_log', u'meta_data_change_log_changed_by_fkey')

	# add metadata change methods
	op.create_table('meta_data_change_methods',
	sa.Column('meta_data_change_method_id', sa.INTEGER(), nullable=False),
	sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
	sa.PrimaryKeyConstraint('meta_data_change_method_id', name=u'meta_data_change_methods_pkey'),
	sa.UniqueConstraint('name', name=u'meta_data_change_methods_name_key')
	)

	op.add_column(u'meta_data_change_requests', sa.Column('meta_data_change_method_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(
		u'meta_data_change_requests_meta_data_change_method_id_fkey',
		'meta_data_change_requests',
		'meta_data_change_methods',
		['meta_data_change_method_id'],
		['meta_data_change_method_id']
	)
	op.add_column(u'meta_data_change_log', sa.Column('meta_data_change_method_id', sa.INTEGER(), autoincrement=False, nullable=False))
	op.create_foreign_key(
		u'meta_data_change_log_meta_data_change_method_id_fkey',
		'meta_data_change_log',
		'meta_data_change_methods',
		['meta_data_change_method_id'],
		['meta_data_change_method_id']
	)


