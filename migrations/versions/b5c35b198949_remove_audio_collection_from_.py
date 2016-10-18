"""remove audio collection from performance meta categories

Revision ID: b5c35b198949
Revises: d625d5d18d7a
Create Date: 2016-09-27 15:45:59.885262

"""

# revision identifiers, used by Alembic.
revision = 'b5c35b198949'
down_revision = 'd625d5d18d7a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index('performance_meta_categories_by_recording_platform_id', 'performance_meta_categories', ['recording_platform_id'], unique=False)
    op.drop_constraint(u'performance_meta_categories_audio_collection_id_name_key', 'performance_meta_categories', type_='unique')
    op.drop_index('performance_meta_categories_by_audio_collection_id', table_name='performance_meta_categories')
    op.create_unique_constraint(u'performance_meta_categories_recording_platform_id_name_key', 'performance_meta_categories', ['recording_platform_id', 'name'])
    op.drop_constraint(u'performance_meta_categories_audio_collection_id_fkey', 'performance_meta_categories', type_='foreignkey')
    op.drop_column(u'performance_meta_categories', 'audio_collection_id')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'performance_meta_categories', sa.Column('audio_collection_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_foreign_key(u'performance_meta_categories_audio_collection_id_fkey', 'performance_meta_categories', 'audio_collections', ['audio_collection_id'], ['audio_collection_id'])
    op.drop_constraint(u'performance_meta_categories_recording_platform_id_name_key', 'performance_meta_categories', type_='unique')
    op.create_index('performance_meta_categories_by_audio_collection_id', 'performance_meta_categories', ['audio_collection_id'], unique=False)
    op.create_unique_constraint(u'performance_meta_categories_audio_collection_id_name_key', 'performance_meta_categories', ['audio_collection_id', 'name'])
    op.drop_index('performance_meta_categories_by_recording_platform_id', table_name='performance_meta_categories')
    ### end Alembic commands ###