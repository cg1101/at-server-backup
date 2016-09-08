"""empty message

Revision ID: 323971271781
Revises: 711072834313
Create Date: 2016-09-08 18:34:27.116666

"""

# revision identifiers, used by Alembic.
revision = '323971271781'
down_revision = '711072834313'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'audio_files', 'duration')
    op.add_column(u'recordings', sa.Column('duration', postgresql.INTERVAL(), nullable=False))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'recordings', 'duration')
    op.add_column(u'audio_files', sa.Column('duration', postgresql.INTERVAL(), autoincrement=False, nullable=False))
    ### end Alembic commands ###
