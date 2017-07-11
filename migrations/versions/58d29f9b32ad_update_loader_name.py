"""update loader name

Revision ID: 58d29f9b32ad
Revises: a0b8134317e7
Create Date: 2016-12-19 22:19:30.073575

"""

# revision identifiers, used by Alembic.
revision = '58d29f9b32ad'
down_revision = 'a0b8134317e7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
	pass # used to be seed data migration


def downgrade():
	pass # used to be seed data migration

