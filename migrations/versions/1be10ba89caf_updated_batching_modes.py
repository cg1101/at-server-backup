"""updated batching modes

Revision ID: 1be10ba89caf
Revises: 0de4dea9470c
Create Date: 2017-01-11 15:29:41.469402

"""

# revision identifiers, used by Alembic.
revision = '1be10ba89caf'
down_revision = '0de4dea9470c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from migrations.seed import is_database_seeded, delete_seed_data, add_seed_data


def upgrade():

	if is_database_seeded():
		from alembic import context
		migrate_context = context.get_context()
		migrate_context.connection.execute(
			sa.text("update batchingmodes set name = :new_name where name = :old_name"),
			new_name="File",
			old_name="Recording"
		)
		migrate_context.connection.execute(
			sa.text("update batchingmodes set name = :new_name where name = :old_name"),
			new_name="Performance",
			old_name="Session"
		)
		delete_seed_data("batchingmodes", "name = :name", name="Long Recordings")


def downgrade():

	if is_database_seeded():
		from alembic import context
		migrate_context = context.get_context()
		migrate_context.connection.execute(
			sa.text("update batchingmodes set name = :new_name where name = :old_name"),
			new_name="Recording",
			old_name="File"
		)
		migrate_context.connection.execute(
			sa.text("update batchingmodes set name = :new_name where name = :old_name"),
			new_name="Session",
			old_name="Performance"
		)
		add_seed_data("batchingmodes", {"name" : "Long Recordings", "requirescontext": True})
