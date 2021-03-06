"""removed database settings

Revision ID: c641c766b860
Revises: cdc06171e041
Create Date: 2017-07-11 16:51:17.280883

"""

# revision identifiers, used by Alembic.
revision = 'c641c766b860'
down_revision = 'cdc06171e041'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('database_settings')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('database_settings',
    sa.Column('seeded', sa.BOOLEAN(), autoincrement=False, nullable=False)
    )
    ### end Alembic commands ###
