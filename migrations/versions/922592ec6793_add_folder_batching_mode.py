"""add folder batching mode

Revision ID: 922592ec6793
Revises: 497be45164f1
Create Date: 2017-06-06 21:27:36.912146

"""

# revision identifiers, used by Alembic.
revision = '922592ec6793'
down_revision = '497be45164f1'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from migrations.seed import delete_seed_data, add_seed_data


def upgrade():
	add_seed_data("batchingmodes", {"name": "Folder"})


def downgrade():
	delete_seed_data("batchingmodes", "name = :name", name="Folder")
