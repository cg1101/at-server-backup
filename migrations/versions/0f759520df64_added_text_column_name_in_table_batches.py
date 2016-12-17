"""added text column name in table batches.

Revision ID: 0f759520df64
Revises: 2f5dbbcfee8e
Create Date: 2016-12-12 09:21:12.612950

"""

# revision identifiers, used by Alembic.
revision = '0f759520df64'
down_revision = '2f5dbbcfee8e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column(u'batches', sa.Column('name', sa.TEXT(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'batches', 'name')
    ### end Alembic commands ###