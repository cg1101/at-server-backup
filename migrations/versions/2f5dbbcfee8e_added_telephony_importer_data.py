"""added telephony importer data

Revision ID: 2f5dbbcfee8e
Revises: d3d6b7e437a8
Create Date: 2016-12-07 19:32:23.754802

"""

# revision identifiers, used by Alembic.
revision = '2f5dbbcfee8e'
down_revision = 'd3d6b7e437a8'
branch_labels = None
depends_on = None

import json
from alembic import op
import sqlalchemy as sa
from migrations.seed import is_database_seeded, add_seed_data, delete_seed_data


def upgrade():
	add_seed_data("recording_platform_types", {"name" : "Telephony"})
	
	if is_database_seeded():
		from alembic import context
		migrate_context = context.get_context()
		migrate_context.connection.execute(
			sa.text("update audio_importers set metadata_sources = :sources where name = :name"),
			sources=json.dumps(["Log File"]),
			name="Appen Telephony - Conversational",
		)


def downgrade():
	delete_seed_data("recording_platform_types", "name = :name", name="Telephony")

	if is_database_seeded():
		from alembic import context
		migrate_context = context.get_context()
		migrate_context.connection.execute(
			sa.text("update audio_importers set metadata_sources = null where name = :name"),
			name="Appen Telephony - Conversational",
		)
