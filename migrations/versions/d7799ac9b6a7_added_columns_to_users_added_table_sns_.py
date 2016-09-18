"""added columns to users, added table sns_message_records

Revision ID: d7799ac9b6a7
Revises: a2c1f3b807f7
Create Date: 2016-09-18 14:23:00.799436

"""

# revision identifiers, used by Alembic.
revision = 'd7799ac9b6a7'
down_revision = 'a2c1f3b807f7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sns_message_records',
    sa.Column('message_id', sa.TEXT(), nullable=False),
    sa.Column('message_type', sa.TEXT(), nullable=False),
    sa.Column('body', sa.TEXT(), nullable=False),
    sa.Column('processed_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.PrimaryKeyConstraint('message_id')
    )
    op.add_column(u'users', sa.Column('active', sa.BOOLEAN(), server_default=sa.text(u'TRUE'), nullable=False))
    op.add_column(u'users', sa.Column('emailaddress', sa.TEXT(), nullable=True))
    op.add_column(u'users', sa.Column('familyname', sa.TEXT(), nullable=True))
    op.add_column(u'users', sa.Column('givenname', sa.TEXT(), nullable=True))
    op.add_column(u'users', sa.Column('global_id', sa.INTEGER(), nullable=True))
    op.create_unique_constraint('users_emailaddress_key', 'users', ['emailaddress'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('users_emailaddress_key', 'users', type_='unique')
    op.drop_column(u'users', 'global_id')
    op.drop_column(u'users', 'givenname')
    op.drop_column(u'users', 'familyname')
    op.drop_column(u'users', 'emailaddress')
    op.drop_column(u'users', 'active')
    op.drop_table('sns_message_records')
    ### end Alembic commands ###
