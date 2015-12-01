"""added level 140 tables batches/calculatedpayments/customutterancegroups/postprocessingutterancegroups/reworkcontenthistory/subtaskmetrics/useworkstats/utteranceselectionfilters

Revision ID: 7b0c1596294
Revises: 40b30f9bb812
Create Date: 2015-11-30 15:13:55.989468

"""

# revision identifiers, used by Alembic.
revision = '7b0c1596294'
down_revision = '40b30f9bb812'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('batches',
    sa.Column('batchid', sa.INTEGER(), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('subtaskid', sa.INTEGER(), nullable=False),
    sa.Column('userid', sa.INTEGER(), nullable=True),
    sa.Column('priority', sa.INTEGER(), server_default=sa.text(u'5'), nullable=False),
    sa.Column('onhold', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=True),
    sa.Column('leasegranted', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('leaseexpires', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('notuserid', sa.INTEGER(), nullable=True),
    sa.Column('workintervalid', sa.INTEGER(), nullable=True),
    sa.Column('checkedout', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.ForeignKeyConstraint(['subtaskid'], [u'subtasks.subtaskid'], name=u'batches_subtaskid_fkey'),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'batches_taskid_fkey'),
    sa.ForeignKeyConstraint(['userid'], [u'users.userid'], name=u'batches_userid_fkey'),
    sa.PrimaryKeyConstraint(u'batchid', name=op.f('pk_batches'))
    )
    op.create_index('batchesbysubtaskid', 'batches', ['subtaskid'], unique=False)
    op.create_index('batchesbytaskid', 'batches', ['taskid'], unique=False)
    op.create_index('batchesbyuserid', 'batches', ['userid'], unique=False)
    op.create_table('calculatedpayments',
    sa.Column('calculatedpaymentid', sa.INTEGER(), nullable=False),
    sa.Column('payrollid', sa.INTEGER(), nullable=False),
    sa.Column('workintervalid', sa.INTEGER(), nullable=False),
    sa.Column('userid', sa.INTEGER(), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('subtaskid', sa.INTEGER(), nullable=False),
    sa.Column('units', sa.INTEGER(), nullable=False),
    sa.Column('unitsqaed', sa.INTEGER(), nullable=False),
    sa.Column('accuracy', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.Column('originalamount', sa.INTEGER(), nullable=False),
    sa.Column('amount', sa.INTEGER(), nullable=False),
    sa.Column('receipt', sa.TEXT(), nullable=True),
    sa.Column('updated', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.Column('items', sa.INTEGER(), nullable=False),
    sa.Column('itemsqaed', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['payrollid'], [u'payrolls.payrollid'], name=u'calculatedpayments_payrollid_fkey'),
    sa.ForeignKeyConstraint(['subtaskid'], [u'subtasks.subtaskid'], name=u'calculatedpayments_subtaskid_fkey'),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'calculatedpayments_taskid_fkey'),
    sa.ForeignKeyConstraint(['userid'], [u'users.userid'], name=u'calculatedpayments_userid_fkey'),
    sa.ForeignKeyConstraint(['workintervalid'], [u'workintervals.workintervalid'], name=u'calculatedpayments_workintervalid_fkey'),
    sa.PrimaryKeyConstraint(u'calculatedpaymentid', name=op.f('pk_calculatedpayments'))
    )
    op.create_table('customutterancegroups',
    sa.Column('groupid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('created', postgresql.TIMESTAMP(), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('utterances', sa.INTEGER(), nullable=False),
    sa.Column('selectionid', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['selectionid'], [u'utteranceselections.selectionid'], name=u'customutterancegroups_selectionid_fkey'),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'customutterancegroups_taskid_fkey'),
    sa.PrimaryKeyConstraint(u'groupid', name=op.f('pk_customutterancegroups'))
    )
    op.create_index('customutterancegroups_taskid_key', 'customutterancegroups', ['taskid', 'name'], unique=True)
    op.create_table('postprocessingutterancegroups',
    sa.Column('groupid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('streamid', sa.INTEGER(), nullable=True),
    sa.Column('created', postgresql.TIMESTAMP(), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('utterances', sa.INTEGER(), nullable=False),
    sa.Column('selectionid', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['selectionid'], [u'utteranceselections.selectionid'], name=u'postprocessingutterancegroups_selectionid_fkey'),
    sa.ForeignKeyConstraint(['taskid'], [u'tasks.taskid'], name=u'postprocessingutterancegroups_taskid_fkey'),
    sa.PrimaryKeyConstraint(u'groupid', name=op.f('pk_postprocessingutterancegroups'))
    )
    op.create_index('postprocessingutterancegroups_taskid_key', 'postprocessingutterancegroups', ['taskid', 'name'], unique=True)
    op.create_table('reworkcontenthistory',
    sa.Column('subtaskid', sa.INTEGER(), nullable=False),
    sa.Column('selectionid', sa.INTEGER(), nullable=True),
    sa.Column('amount', sa.INTEGER(), nullable=False),
    sa.Column('populating', sa.BOOLEAN(), server_default=sa.text(u'true'), nullable=True),
    sa.Column('t_processed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('operator', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['selectionid'], [u'utteranceselections.selectionid'], name=u'reworkcontenthistory_selectionid_fkey'),
    sa.ForeignKeyConstraint(['subtaskid'], [u'subtasks.subtaskid'], name=u'reworkcontenthistory_subtaskid_fkey')
    )
    op.create_table('subtaskmetrics',
    sa.Column('metricid', sa.INTEGER(), nullable=False),
    sa.Column('userid', sa.INTEGER(), nullable=False),
    sa.Column('workintervalid', sa.INTEGER(), nullable=True),
    sa.Column('subtaskid', sa.INTEGER(), nullable=True),
    sa.Column('amount', sa.INTEGER(), nullable=True),
    sa.Column('words', sa.INTEGER(), nullable=True),
    sa.Column('workrate', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.Column('accuracy', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.Column('lastupdated', postgresql.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['subtaskid'], [u'subtasks.subtaskid'], name=u'subtaskmetrics_subtaskid_fkey'),
    sa.ForeignKeyConstraint(['userid'], [u'users.userid'], name=u'subtaskmetrics_userid_fkey'),
    sa.ForeignKeyConstraint(['workintervalid'], [u'workintervals.workintervalid'], name=u'subtaskmetrics_workintervalid_fkey'),
    sa.PrimaryKeyConstraint(u'metricid', name=op.f('pk_subtaskmetrics'))
    )
    op.create_index('subtaskmetricsbysubtaskid', 'subtaskmetrics', ['subtaskid'], unique=False)
    op.create_index('subtaskmetricsbyuserid', 'subtaskmetrics', ['userid'], unique=False)
    op.create_index('subtaskmetricsbyworkintervalid', 'subtaskmetrics', ['workintervalid'], unique=False)
    op.create_table('userworkstats',
    sa.Column('workintervalid', sa.INTEGER(), nullable=False),
    sa.Column('taskid', sa.INTEGER(), nullable=False),
    sa.Column('subtaskid', sa.INTEGER(), nullable=False),
    sa.Column('userid', sa.INTEGER(), nullable=False),
    sa.Column('items', sa.INTEGER(), nullable=False),
    sa.Column('itemsqaed', sa.INTEGER(), nullable=False),
    sa.Column('units', sa.INTEGER(), nullable=False),
    sa.Column('unitsqaed', sa.INTEGER(), nullable=False),
    sa.Column('accuracy', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.ForeignKeyConstraint(['userid'], [u'users.userid'], name=u'userworkstats_userid_fkey'),
    sa.ForeignKeyConstraint(['workintervalid'], [u'workintervals.workintervalid'], name=u'userworkstats_workintervalid_fkey')
    )
    op.create_table('utteranceselectionfilters',
    sa.Column('filterid', sa.INTEGER(), nullable=False),
    sa.Column('selectionid', sa.INTEGER(), nullable=False),
    sa.Column('include', sa.BOOLEAN(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=False),
    sa.Column('filtertype', sa.TEXT(), nullable=False),
    sa.Column('mandatory', sa.BOOLEAN(), nullable=False),
    sa.ForeignKeyConstraint(['selectionid'], [u'utteranceselections.selectionid'], name=u'utteranceselectionfilters_selectionid_fkey'),
    sa.PrimaryKeyConstraint(u'filterid', name=op.f('pk_utteranceselectionfilters'))
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('utteranceselectionfilters')
    op.drop_table('userworkstats')
    op.drop_index('subtaskmetricsbyworkintervalid', table_name='subtaskmetrics')
    op.drop_index('subtaskmetricsbyuserid', table_name='subtaskmetrics')
    op.drop_index('subtaskmetricsbysubtaskid', table_name='subtaskmetrics')
    op.drop_table('subtaskmetrics')
    op.drop_table('reworkcontenthistory')
    op.drop_index('postprocessingutterancegroups_taskid_key', table_name='postprocessingutterancegroups')
    op.drop_table('postprocessingutterancegroups')
    op.drop_index('customutterancegroups_taskid_key', table_name='customutterancegroups')
    op.drop_table('customutterancegroups')
    op.drop_table('calculatedpayments')
    op.drop_index('batchesbyuserid', table_name='batches')
    op.drop_index('batchesbytaskid', table_name='batches')
    op.drop_index('batchesbysubtaskid', table_name='batches')
    op.drop_table('batches')
    ### end Alembic commands ###