"""populate loader config

Revision ID: 33a9b8b04fde
Revises: e868e53ac49a
Create Date: 2017-06-23 16:09:48.761298

"""

# revision identifiers, used by Alembic.
revision = '33a9b8b04fde'
down_revision = 'e868e53ac49a'
branch_labels = None
depends_on = None

import json
from alembic import op
import sqlalchemy as sa


def upgrade():
	conn = op.get_bind()

	# update tasks
	res = conn.execute("select taskid, config from tasks where config is not null")
	results = res.fetchall()

	for task_id, config in results:
		if config and "loader" in config:
			op.execute("update tasks set loader = '{0}' where taskid = {1}".format(json.dumps(config["loader"]), task_id))
			del config["loader"]
			op.execute("update tasks set config = '{0}' where taskid = {1}".format(json.dumps(config), task_id))

	# update recording platforms
	op.execute("update recording_platforms set loader = config")
	op.execute("update recording_platforms set config = null")


def downgrade():
	conn = op.get_bind()

	# update tasks
	res = conn.execute("select taskid, config, loader from tasks where loader is not null")
	results = res.fetchall()

	for task_id, config, loader in results:
		if loader:
			if config:
				config["loader"] = loader
			else:
				config = {"loader": loader}

			op.execute("update tasks set loader = null, config = '{0}' where taskid = {1}".format(json.dumps(config), task_id))

	# update recording platforms
	op.execute("update recording_platforms set config = loader")
	op.execute("update recording_platforms set loader = null")
