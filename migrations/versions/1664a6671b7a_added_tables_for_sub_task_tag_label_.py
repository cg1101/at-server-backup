"""added tables for sub task tag/label customization

Revision ID: 1664a6671b7a
Revises: 0f759520df64
Create Date: 2016-12-12 13:15:44.157572

"""

# revision identifiers, used by Alembic.
revision = '1664a6671b7a'
down_revision = '0f759520df64'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('shadowedlabels',
    sa.Column('subtaskid', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('labelid', sa.Integer(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('subtaskid', 'labelid')
    )
    op.create_table('shadowedtags',
    sa.Column('subtaskid', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('tagid', sa.Integer(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('subtaskid', 'tagid')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('shadowedtags')
    op.drop_table('shadowedlabels')
    ### end Alembic commands ###
