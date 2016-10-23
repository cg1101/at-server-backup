"""remove index, name from recording platform

Revision ID: f25f34116907
Revises: a1c393e7254f
Create Date: 2016-10-23 12:07:39.392542

"""

# revision identifiers, used by Alembic.
revision = 'f25f34116907'
down_revision = 'a1c393e7254f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_column(u'recording_platforms', 'index')
    op.drop_column(u'recording_platforms', 'name')


def downgrade():
    op.add_column(u'recording_platforms', sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False))
    op.add_column(u'recording_platforms', sa.Column('index', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_unique_constraint(u'recording_platforms_audio_collection_id_name_key', 'recording_platforms', ['audio_collection_id', 'name'])
    op.create_unique_constraint(u'recording_platforms_audio_collection_id_index_key', 'recording_platforms', ['audio_collection_id', 'index'])
