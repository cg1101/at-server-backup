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


def upgrade():
	pass # used to be seed data migration


def downgrade():
	pass # used to be seed data migration

