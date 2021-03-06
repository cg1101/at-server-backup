"""added level 110 tables calculateduserpayrates/tasks/tracking_events

Revision ID: 2a3beeb0b80c
Revises: 44ea2a2d8d1f
Create Date: 2015-11-30 14:15:18.167517

"""

# revision identifiers, used by Alembic.
revision = '2a3beeb0b80c'
down_revision = '44ea2a2d8d1f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tracking_events',
    sa.Column('eventid', sa.INTEGER(), nullable=False),
    sa.Column('eventtype', sa.TEXT(), nullable=False),
    sa.Column('userid', sa.INTEGER(), nullable=False),
    sa.Column('t_triggered_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('hostip', postgresql.INET(), nullable=True),
    sa.Column('details', sa.TEXT(), nullable=False),
    sa.PrimaryKeyConstraint(u'eventid', name=op.f('pk_tracking_events'))
    )
    op.create_table('calculateduserpayrates',
    sa.Column('rateid', sa.INTEGER(), nullable=False),
    sa.Column('userid', sa.INTEGER(), nullable=False),
    sa.Column('hourlyrate', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.Column('t', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('changerid', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['changerid'], [u'users.userid'], name=u'calculateduserpayrates_changerid_fkey'),
    sa.ForeignKeyConstraint(['rateid'], [u'rates.rateid'], name=u'calculateduserpayrates_rateid_fkey'),
    sa.ForeignKeyConstraint(['userid'], [u'users.userid'], name=u'calculateduserpayrates_userid_fkey')
    )
    op.create_table('tasks',
    sa.Column('taskid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('projectid', sa.INTEGER(), nullable=False),
    sa.Column('tasktypeid', sa.INTEGER(), nullable=False),
    sa.Column('status', sa.TEXT(), server_default=sa.text(u"'active'::text"), nullable=False),
    sa.Column('src_dir', sa.CHAR(length=3), server_default=sa.text(u"'ltr'::bpchar"), nullable=False),
    sa.Column('laststatuschange', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('tagsetid', sa.INTEGER(), nullable=True),
    sa.Column('labelsetid', sa.INTEGER(), nullable=True),
    sa.Column('migrated', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('migratedby', sa.INTEGER(), nullable=True),
    sa.Column('handlerid', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['handlerid'], [u'filehandlers.handlerid'], name=u'tasks_handlerid_fkey'),
    sa.ForeignKeyConstraint(['labelsetid'], [u'labelsets.labelsetid'], name=u'tasks_labelsetid_fkey'),
    sa.ForeignKeyConstraint(['migratedby'], [u'users.userid'], name=u'tasks_migratedby_fkey'),
    sa.ForeignKeyConstraint(['projectid'], [u'projects.projectid'], name=u'tasks_projectid_fkey'),
    sa.ForeignKeyConstraint(['tagsetid'], [u'tagsets.tagsetid'], name=u'tasks_tagsetid_fkey'),
    sa.ForeignKeyConstraint(['tasktypeid'], [u'tasktypes.tasktypeid'], name=u'tasks_tasktypeid_fkey'),
    sa.PrimaryKeyConstraint(u'taskid', name=op.f('pk_tasks')),
    sa.CheckConstraint("src_dir=ANY(ARRAY['ltr','rtl'])"),
    sa.CheckConstraint("status=ANY(ARRAY['active','disabled','finished','closed','archived'])"),
    )
    op.create_index(op.f('ix_tasks_migratedby'), 'tasks', ['migratedby'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_tasks_migratedby'), table_name='tasks')
    op.drop_table('tasks')
    op.drop_table('calculateduserpayrates')
    op.drop_table('tracking_events')
    ### end Alembic commands ###
