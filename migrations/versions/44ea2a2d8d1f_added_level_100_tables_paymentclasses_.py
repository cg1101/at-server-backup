"""added level 100 tables paymentclasses/paymenttypes/payrolls/projects/users

Revision ID: 44ea2a2d8d1f
Revises: 1d1130e793f4
Create Date: 2015-11-30 14:12:01.342549

"""

# revision identifiers, used by Alembic.
revision = '44ea2a2d8d1f'
down_revision = '1d1130e793f4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('paymentclasses',
    sa.Column('paymentclassid', sa.INTEGER(), nullable=True)
    )
    op.create_table('paymenttypes',
    sa.Column('paymenttypeid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint(u'paymenttypeid', name=op.f('pk_paymenttypes'))
    )
    op.create_table('payrolls',
    sa.Column('payrollid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('updatedpayments', postgresql.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint(u'payrollid', name=op.f('pk_payrolls'))
    )
    op.create_table('users',
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint(u'userid', name=op.f('pk_users'))
    )
    op.create_table('projects',
    sa.Column('projectid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('created', postgresql.TIMESTAMP(), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('migratedby', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['migratedby'], [u'users.userid'], name=u'projects_migratedby_fkey'),
    sa.PrimaryKeyConstraint(u'projectid', name=op.f('pk_projects'))
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('payrolls')
    op.drop_table('paymenttypes')
    op.drop_table('paymentclasses')
    ### end Alembic commands ###
