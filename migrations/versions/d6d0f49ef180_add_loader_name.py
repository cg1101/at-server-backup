"""add loader name

Revision ID: d6d0f49ef180
Revises: ae596990f8ae
Create Date: 2017-06-23 15:32:47.967443

"""

# revision identifiers, used by Alembic.
revision = 'd6d0f49ef180'
down_revision = 'ae596990f8ae'
branch_labels = None
depends_on = None

import json
from alembic import op
import sqlalchemy as sa


def upgrade():
	conn = op.get_bind()

	# update tasks
	res = conn.execute("select taskid, loaders.name, config from tasks join loaders using (loader_id)")
	results = res.fetchall()

	for task_id, loader_name, config in results:

		if config: 
			if "loader" in config:
				config["loader"]["name"] = loader_name
			else:
				config.setdefault("loader", {})["name"] = loader_name
		else:
			config = {}
			config.setdefault("loader", {})["name"] = loader_name

		op.execute("update tasks set config = '{0}' where taskid = {1}".format(json.dumps(config), task_id))

	# update recording platforms
	res = conn.execute("select recording_platform_id, loaders.name, config from recording_platforms join loaders using (loader_id)")
	results = res.fetchall()

	for recording_platform_id, loader_name, config in results:

		if config:
			config["name"] = loader_name
		else:
			config = {"name": loader_name}
		
		op.execute("update recording_platforms set config = '{0}' where recording_platform_id = {1}".format(json.dumps(config), recording_platform_id))


def downgrade():
	conn = op.get_bind()

	# update tasks
	res = conn.execute("select taskid, loaders.name, config from tasks join loaders using (loader_id)")
	results = res.fetchall()

	for task_id, loader_name, config in results:

		if config and "loader" in config and "name" in config["loader"]:
			del config["loader"]["name"]
			
			op.execute("update tasks set config = '{0}' where taskid = {1}".format(json.dumps(config), task_id))

	# update recording platforms
	res = conn.execute("select recording_platform_id, loaders.name, config from recording_platforms join loaders using (loader_id)")
	results = res.fetchall()

	for recording_platform_id, loader_name, config in results:

		if config:
			del config["name"]
			op.execute("update recording_platforms set config = '{0}' where recording_platform_id = {1}".format(json.dumps(config), recording_platform_id))

