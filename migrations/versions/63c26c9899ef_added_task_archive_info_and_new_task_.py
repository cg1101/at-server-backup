"""added task archive info and new task types

Revision ID: 63c26c9899ef
Revises: 594fde873e6c
Create Date: 2016-11-21 16:24:11.454113

"""

# revision identifiers, used by Alembic.
revision = '63c26c9899ef'
down_revision = '594fde873e6c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from migrations.seed import add_seed_data, delete_seed_data

def upgrade():
	op.add_column(u'tasks', sa.Column('archive_info', postgresql.JSONB(), nullable=True))
	add_seed_data("tasktypes", {"name" : "audio checking"})
	add_seed_data("tasktypes", {"name" : "transcription"})

def downgrade():
	delete_seed_data("tasktypes", "name = :name", name="transcription")
	delete_seed_data("tasktypes", "name = :name", name="audio checking")
	op.drop_column(u'tasks', 'archive_info')
