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
from migrations.seed import is_database_seeded


def upgrade():
	if is_database_seeded():
		from alembic import context
		migrate_context = context.get_context()
		migrate_context.connection.execute(
			sa.text("update loaders set name = :new_name where name = :old_name"),
			old_name="From Audio Checking",
			new_name="Linked",
		)


def downgrade():
	if is_database_seeded():
		from alembic import context
		migrate_context = context.get_context()
		migrate_context.connection.execute(
			sa.text("update loaders set name = :new_name where name = :old_name"),
			old_name="Linked",
			new_name="From Audio Checking",
		)
