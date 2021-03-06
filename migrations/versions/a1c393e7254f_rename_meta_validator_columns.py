"""rename meta validator columns

Revision ID: a1c393e7254f
Revises: b5c35b198949
Create Date: 2016-10-21 15:08:09.095367

"""

# revision identifiers, used by Alembic.
revision = 'a1c393e7254f'
down_revision = 'b5c35b198949'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(u'album_meta_categories', 'validator', new_column_name='validator_spec')
    op.alter_column(u'speaker_meta_categories', 'validator', new_column_name='validator_spec')
    op.alter_column(u'performance_meta_categories', 'validator', new_column_name='validator_spec')
    op.alter_column(u'recording_meta_categories', 'validator', new_column_name='validator_spec')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(u'album_meta_categories', 'validator_spec', new_column_name='validator')
    op.alter_column(u'speaker_meta_categories', 'validator_spec', new_column_name='validator')
    op.alter_column(u'performance_meta_categories', 'validator_spec', new_column_name='validator')
    op.alter_column(u'recording_meta_categories', 'validator_spec', new_column_name='validator')
    ### end Alembic commands ###
