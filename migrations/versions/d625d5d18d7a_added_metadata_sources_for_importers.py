"""added metadata sources for importers

Revision ID: d625d5d18d7a
Revises: 15d803310916
Create Date: 2016-09-26 16:04:46.902966

"""

# revision identifiers, used by Alembic.
revision = 'd625d5d18d7a'
down_revision = '15d803310916'
branch_labels = None
depends_on = None

import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.seed import is_database_seeded


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'audio_importers', sa.Column('metadata_sources', postgresql.JSONB(), nullable=True))
    ### end Alembic commands ###

    if is_database_seeded():
        from alembic import context
        migrate_context = context.get_context()
        migrate_context.connection.execute(
            sa.text("update audio_importers set metadata_sources = :sources where name = :name"),
            sources=json.dumps(["Log File"]),
            name="Appen Mobile Recorder - Scripted",
        )

def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'audio_importers', 'metadata_sources')
    ### end Alembic commands ###
