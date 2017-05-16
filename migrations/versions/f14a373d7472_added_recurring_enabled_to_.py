"""added recurring/enabled to utteranceselections table to support recurring selection.

Revision ID: f14a373d7472
Revises: f74888f5f13a
Create Date: 2017-05-16 14:11:26.485918

"""

# revision identifiers, used by Alembic.
revision = 'f14a373d7472'
down_revision = 'f74888f5f13a'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'utteranceselections', sa.Column('recurring', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=True))
    op.add_column(u'utteranceselections', sa.Column('enabled', sa.BOOLEAN(), server_default=sa.text(u'true'), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'utteranceselections', 'enabled')
    op.drop_column(u'utteranceselections', 'recurring')
    ### end Alembic commands ###
