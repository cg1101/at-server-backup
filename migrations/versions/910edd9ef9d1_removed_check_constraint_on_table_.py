"""removed check constraint on table reworkcontenthistory.

Revision ID: 910edd9ef9d1
Revises: 1be10ba89caf
Create Date: 2017-01-25 12:07:35.618907

"""

# revision identifiers, used by Alembic.
revision = '910edd9ef9d1'
down_revision = '1be10ba89caf'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('reworkcontenthistory_check', 'reworkcontenthistory', type_='check')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_check_constraint('reworkcontenthistory_check', 'reworkcontenthistory',
        text('populating AND selectionid IS NOT NULL OR NOT populating AND selectionid IS NULL'),
    )
    ### end Alembic commands ###
