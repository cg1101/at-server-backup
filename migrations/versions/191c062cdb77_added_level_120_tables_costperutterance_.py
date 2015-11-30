"""added level 120 tables costperutterance/loads/otherpayments/overallqaprogresscache/overalltrprogresscache/overallworkprogresscache/streams/subtasks/taskerrortypes/taskreports

Revision ID: 191c062cdb77
Revises: 2a3beeb0b80c
Create Date: 2015-11-30 14:34:06.505772

"""

# revision identifiers, used by Alembic.
revision = '191c062cdb77'
down_revision = '2a3beeb0b80c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('costperutterance',
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('cutofftime', postgresql.TIMESTAMP(), nullable=False),
    sa.Column('itemsdone', sa.INTEGER(), nullable=False),
    sa.Column('unitsdone', sa.INTEGER(), nullable=False),
    sa.Column('payrollid', sa.INTEGER(), nullable=False),
    sa.Column('amount', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.ForeignKeyConstraint(['payrollid'], [u'payrolls.payrollid'], name=u'costperutterance_payrollid_fkey'),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'costperutterance_taskid_fkey'),
    sa.PrimaryKeyConstraint(u'taskid', u'payrollid', name=op.f('pk_costperutterance'))
    )
    op.create_index('costperutterancebytaskid', 'costperutterance', ['taskid'], unique=False)
    op.create_table('loads',
    sa.Column('loadid', sa.INTEGER(), nullable=False),
    sa.Column('createdby', sa.INTEGER(), nullable=False),
    sa.Column('createdat', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['createdby'], [u'users.userid'], name=op.f('fk_loads_createdby_users')),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=op.f('fk_loads_taskid_tasks')),
    sa.PrimaryKeyConstraint(u'loadid', name=op.f('pk_loads'))
    )
    op.create_index('ix_loads_taskid_loadid', 'loads', ['loadid', 'taskid'], unique=True)
    op.create_table('otherpayments',
    sa.Column('otherpaymentid', sa.INTEGER(), nullable=False),
    sa.Column('payrollid', sa.INTEGER(), nullable=False),
    sa.Column('identifier', sa.TEXT(), nullable=False),
    sa.Column('paymenttypeid', sa.INTEGER(), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('userid', sa.INTEGER(), nullable=False),
    sa.Column('amount', sa.INTEGER(), nullable=False),
    sa.Column('added', postgresql.TIMESTAMP(), server_default=sa.text(u'now()'), nullable=False),
    sa.ForeignKeyConstraint(['paymenttypeid'], [u'paymenttypes.paymenttypeid'], name=u'otherpayments_paymenttypeid_fkey'),
    sa.ForeignKeyConstraint(['payrollid'], [u'payrolls.payrollid'], name=u'otherpayments_payrollid_fkey'),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'otherpayments_taskid_fkey'),
    sa.ForeignKeyConstraint(['userid'], [u'users.userid'], name=u'otherpayments_userid_fkey'),
    sa.PrimaryKeyConstraint(u'otherpaymentid', name=op.f('pk_otherpayments'))
    )
    op.create_index('otherpayments_identifier_key', 'otherpayments', ['identifier'], unique=True)
    op.create_index('otherpaymentsbypayrollid', 'otherpayments', ['payrollid'], unique=False)
    op.create_index('otherpaymentsbytaskid', 'otherpayments', ['taskid'], unique=False)
    op.create_table('overallqaprogresscache',
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('endtime', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('remaining', sa.INTEGER(), nullable=False),
    sa.Column('lastupdated', postgresql.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'overallqaprogresscache_taskid_fkey'),
    sa.PrimaryKeyConstraint(u'taskid', name=op.f('pk_overallqaprogresscache'))
    )
    op.create_table('overalltrprogresscache',
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('itemcount', sa.INTEGER(), nullable=False),
    sa.Column('wordcount', sa.INTEGER(), nullable=False),
    sa.Column('newitems', sa.INTEGER(), nullable=False),
    sa.Column('finished', sa.INTEGER(), nullable=False),
    sa.Column('finishedlastweek', sa.INTEGER(), nullable=False),
    sa.Column('lastupdated', postgresql.TIMESTAMP(), nullable=False),
    sa.Column('overallaccuracy', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'overalltrprogresscache_taskid_fkey')
    )
    op.create_table('overallworkprogresscache',
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('total', sa.INTEGER(), nullable=False),
    sa.Column('newutts', sa.INTEGER(), nullable=False),
    sa.Column('transcribed', sa.INTEGER(), nullable=False),
    sa.Column('transcribedlastweek', sa.INTEGER(), nullable=False),
    sa.Column('lastupdated', postgresql.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'overallworkprogresscache_taskid_fkey'),
    sa.PrimaryKeyConstraint(u'taskid', name=op.f('pk_overallworkprogresscache'))
    )
    op.create_table('streams',
    sa.Column('streamid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('created', postgresql.TIMESTAMP(), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('open', sa.BOOLEAN(), server_default=sa.text(u'true'), nullable=False),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'streams_taskid_fkey'),
    sa.PrimaryKeyConstraint(u'streamid', name=op.f('pk_streams'))
    )
    op.create_index('streams_taskid_key', 'streams', ['taskid', 'name'], unique=True)
    op.create_table('subtasks',
    sa.Column('subtaskid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('worktypeid', sa.INTEGER(), nullable=False),
    sa.Column('maximumpagesize', sa.INTEGER(), server_default=sa.text(u'20'), nullable=False),
    sa.Column('dst_dir', sa.CHAR(length=3), server_default=sa.text(u"'ltr'::bpchar"), nullable=False),
    sa.Column('modeid', sa.INTEGER(), server_default=sa.text(u'1'), nullable=False),
    sa.Column('getpolicy', sa.TEXT(), server_default=sa.text(u"'nolimit'::text"), nullable=True),
    sa.Column('expirypolicy', sa.TEXT(), server_default=sa.text(u"'noextend'::text"), nullable=True),
    sa.Column('allowpageskip', sa.BOOLEAN(), server_default=sa.text(u'true'), nullable=True),
    sa.Column('needitemcontext', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=True),
    sa.Column('allowediting', sa.BOOLEAN(), server_default=sa.text(u'true'), nullable=True),
    sa.Column('allowabandon', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=True),
    sa.Column('lookahead', sa.INTEGER(), server_default=sa.text(u'0'), nullable=False),
    sa.Column('lookbehind', sa.INTEGER(), server_default=sa.text(u'0'), nullable=False),
    sa.Column('allowcheckout', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.Column('is2ndpassqa', sa.BOOLEAN(), nullable=True),
    sa.Column('defaultleaselife', postgresql.INTERVAL(), server_default=sa.text(u"'7 days'::interval"), nullable=True),
    sa.Column('needdynamictagset', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=True),
    sa.Column('instructionspage', sa.TEXT(), nullable=True),
    sa.Column('useqahistory', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.Column('meanamount', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.Column('maxamount', sa.INTEGER(), nullable=True),
    sa.Column('accuracy', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.Column('maxworkrate', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.Column('medianworkrate', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.Column('hidelabels', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=True),
    sa.Column('validators', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['modeid'], [u'batchingmodes.modeid'], name=u'subtasks_modeid_fkey'),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'subtasks_taskid_fkey'),
    sa.ForeignKeyConstraint(['worktypeid'], [u'worktypes.worktypeid'], name=u'subtasks_worktypeid_fkey'),
    sa.PrimaryKeyConstraint(u'subtaskid', name=op.f('pk_subtasks'))
    )
    op.create_index('ix_subtasks_subtaskid', 'subtasks', ['taskid'], unique=False)
    op.create_index(op.f('ix_subtasks_taskid'), 'subtasks', ['taskid', 'worktypeid', 'name'], unique=True)
    op.create_index('ix_subtasks_taskid_subtaskid', 'subtasks', ['taskid', 'subtaskid'], unique=True)
    op.create_table('taskerrortypes',
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('errortypeid', sa.INTEGER(), nullable=False),
    sa.Column('severity', postgresql.DOUBLE_PRECISION(), server_default=sa.text(u'1'), nullable=False),
    sa.Column('disabled', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.ForeignKeyConstraint(['errortypeid'], [u'errortypes.errortypeid'], name=u'taskerrortypes_errortypeid_fkey'),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'taskerrortypes_taskid_fkey'),
    sa.PrimaryKeyConstraint(u'taskid', u'errortypeid', name=op.f('pk_taskerrortypes'))
    )
    op.create_table('taskreports',
    sa.Column('taskreportid', sa.INTEGER(), nullable=False),
    sa.Column('reporttypeid', sa.INTEGER(), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('filename', sa.TEXT(), nullable=True),
    sa.Column('title', sa.TEXT(), nullable=True),
    sa.Column('usergroupid', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['reporttypeid'], [u'taskreporttypes.reporttypeid'], name=u'taskreports_reporttypeid_fkey'),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'taskreports_taskid_fkey'),
    sa.PrimaryKeyConstraint(u'taskreportid', name=op.f('pk_taskreports'))
    )
    op.create_index('taskreportsbytaskid', 'taskreports', ['taskid'], unique=False)
    op.create_table('tasksupervisors',
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('userid', sa.INTEGER(), nullable=False),
    sa.Column('receivesfeedback', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.Column('informloads', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'tasksupervisors_taskid_fkey'),
    sa.ForeignKeyConstraint(['userid'], [u'users.userid'], name=u'tasksupervisors_userid_fkey'),
    sa.PrimaryKeyConstraint(u'taskid', u'userid', name=op.f('pk_tasksupervisors'))
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tasksupervisors')
    op.drop_index('taskreportsbytaskid', table_name='taskreports')
    op.drop_table('taskreports')
    op.drop_table('taskerrortypes')
    op.drop_index('ix_subtasks_taskid_subtaskid', table_name='subtasks')
    op.drop_index(op.f('ix_subtasks_taskid'), table_name='subtasks')
    op.drop_index('ix_subtasks_subtaskid', table_name='subtasks')
    op.drop_table('subtasks')
    op.drop_index('streams_taskid_key', table_name='streams')
    op.drop_table('streams')
    op.drop_table('overallworkprogresscache')
    op.drop_table('overalltrprogresscache')
    op.drop_table('overallqaprogresscache')
    op.drop_index('otherpaymentsbytaskid', table_name='otherpayments')
    op.drop_index('otherpaymentsbypayrollid', table_name='otherpayments')
    op.drop_index('otherpayments_identifier_key', table_name='otherpayments')
    op.drop_table('otherpayments')
    op.drop_index('ix_loads_taskid_loadid', table_name='loads')
    op.drop_table('loads')
    op.drop_index('costperutterancebytaskid', table_name='costperutterance')
    op.drop_table('costperutterance')
    ### end Alembic commands ###
