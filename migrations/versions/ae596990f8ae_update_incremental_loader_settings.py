"""update incremental loader settings

Revision ID: ae596990f8ae
Revises: 808403cc111d
Create Date: 2017-06-23 13:10:33.318207

"""

# revision identifiers, used by Alembic.
revision = 'ae596990f8ae'
down_revision = '808403cc111d'
branch_labels = None
depends_on = None

import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	conn = op.get_bind()
	res = conn.execute("select taskid, config from tasks where config is not null")
	results = res.fetchall()

	for task_id, config in results:
		if config and "loader" in config:
			updated = False

			if "folderUpload" in config["loader"]:
				config["loader"]["incrementalFolderUpload"] = config["loader"]["folderUpload"]
				del config["loader"]["folderUpload"]
				updated = True

			if "incrementalUpload" in config["loader"]:
				config["loader"]["incrementalFileUpload"] = config["loader"]["incrementalUpload"]
				del config["loader"]["incrementalUpload"]
				updated = True

			if updated:
				op.execute("update tasks set config = '{0}' where taskid = {1}".format(json.dumps(config), task_id))
			
			
def downgrade():
	conn = op.get_bind()
	res = conn.execute("select taskid, config from tasks where config is not null")
	results = res.fetchall()

	for task_id, config in results:
		if config and "loader" in config:
			updated = False

			if "incrementalFolderUpload" in config["loader"]:
				config["loader"]["folderUpload"] = config["loader"]["incrementalFolderUpload"]
				del config["loader"]["incrementalFolderUpload"]
				updated = True

			if "incrementalFileUpload" in config["loader"]:
				config["loader"]["incrementalUpload"] = config["loader"]["incrementalFileUpload"]
				del config["loader"]["incrementalFileUpload"]
				updated = True

			if updated:
				op.execute("update tasks set config = '{0}' where taskid = {1}".format(json.dumps(config), task_id))
