"""removed loaders table

Revision ID: e868e53ac49a
Revises: d6d0f49ef180
Create Date: 2017-06-23 16:02:49.010462

"""

# revision identifiers, used by Alembic.
revision = 'e868e53ac49a'
down_revision = 'd6d0f49ef180'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'recording_platforms', sa.Column('loader', postgresql.JSONB(), nullable=True))
	op.drop_constraint(u'recording_platforms_loader_id_fkey', 'recording_platforms', type_='foreignkey')
	op.drop_column(u'recording_platforms', 'loader_id')
	op.add_column(u'tasks', sa.Column('loader', postgresql.JSONB(), nullable=True))
	op.drop_constraint(u'tasks_loader_id_fkey', 'tasks', type_='foreignkey')
	op.drop_column(u'tasks', 'loader_id')
	op.drop_table('loaders')


def downgrade():
	op.create_table('loaders',
	sa.Column('loader_id', sa.INTEGER(), nullable=False),
	sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
	sa.Column('all_performances_incomplete', sa.BOOLEAN(), autoincrement=False, nullable=True),
	sa.Column('metadata_sources', postgresql.JSONB(), autoincrement=False, nullable=True),
	sa.PrimaryKeyConstraint('loader_id', name=u'loaders_pkey'),
	sa.UniqueConstraint('name', name=u'loaders_name_key')
	)
	op.add_column(u'tasks', sa.Column('loader_id', sa.INTEGER(), autoincrement=False, nullable=True))
	op.create_foreign_key(u'tasks_loader_id_fkey', 'tasks', 'loaders', ['loader_id'], ['loader_id'])
	op.drop_column(u'tasks', 'loader')
	op.add_column(u'recording_platforms', sa.Column('loader_id', sa.INTEGER(), autoincrement=False, nullable=True))
	op.create_foreign_key(u'recording_platforms_loader_id_fkey', 'recording_platforms', 'loaders', ['loader_id'], ['loader_id'])
	op.drop_column(u'recording_platforms', 'loader')

