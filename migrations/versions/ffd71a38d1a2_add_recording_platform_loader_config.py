"""add recording platform loader config

Revision ID: ffd71a38d1a2
Revises: 33a9b8b04fde
Create Date: 2017-06-23 16:50:41.659545

"""

# revision identifiers, used by Alembic.
revision = 'ffd71a38d1a2'
down_revision = '33a9b8b04fde'
branch_labels = None
depends_on = None

import json
from alembic import op
import sqlalchemy as sa


def upgrade():
	conn = op.get_bind()
	res = conn.execute("select recording_platform_id, loader, storage_location, master_script_file from recording_platforms")
	results = res.fetchall()

	for recording_platform_id, loader, storage_location, master_script_file in results:
		if not loader:
			loader = {}

		if storage_location:
			loader["storageLocation"] = storage_location

		if master_script_file:
			loader["masterScriptFile"] = master_script_file

		if loader:
			op.execute("update recording_platforms set loader = '{0}' where recording_platform_id = {1}".format(json.dumps(loader), recording_platform_id))


def downgrade():
	pass
