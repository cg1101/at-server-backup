"""remove audio collections

Revision ID: ad237d80941c
Revises: ec1bce61b5ea
Create Date: 2016-11-21 22:14:15.478171

"""

# revision identifiers, used by Alembic.
revision = 'ad237d80941c'
down_revision = 'ec1bce61b5ea'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.drop_table('audio_collections')
    op.drop_table('audio_collection_statuses')


def downgrade():
    op.create_table('audio_collection_statuses',
    sa.Column('audio_collection_status_id', sa.INTEGER(), server_default=sa.text(u"nextval('audio_collection_statuses_audio_collection_status_id_seq'::regclass)"), nullable=False),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('audio_collection_status_id', name=u'audio_collection_statuses_pkey'),
    sa.UniqueConstraint('name', name=u'audio_collection_statuses_name_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('audio_collections',
    sa.Column('audio_collection_id', sa.INTEGER(), nullable=False),
    sa.Column('project_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('key', sa.VARCHAR(length=6), autoincrement=False, nullable=True),
    sa.Column('audio_collection_status_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('archive_file', sa.TEXT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['audio_collection_status_id'], [u'audio_collection_statuses.audio_collection_status_id'], name=u'audio_collections_audio_collection_status_id_fkey'),
    sa.ForeignKeyConstraint(['project_id'], [u'projects.projectid'], name=u'audio_collections_project_id_fkey'),
    sa.PrimaryKeyConstraint('audio_collection_id', name=u'audio_collections_pkey'),
    sa.UniqueConstraint('project_id', 'name', name=u'audio_collections_project_id_name_key')
    )
