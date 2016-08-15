"""added level 010 tables batchingmodes/errorclasses/filehandlers/jobs/labelsets/rates/tagimagepreviews/tagsets/tasktypes/taskreporttypes/worktypes

Revision ID: 4be0f87ef6cb
Revises: 482f574e96c5
Create Date: 2015-11-30 14:05:07.827850

"""

# revision identifiers, used by Alembic.
revision = '4be0f87ef6cb'
down_revision = '482f574e96c5'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('batchingmodes',
    sa.Column('modeid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('requirescontext', sa.BOOLEAN(), server_default=sa.text(u'true'), nullable=False),
    sa.PrimaryKeyConstraint(u'modeid', name=op.f('pk_batchingmodes'))
    )
    op.create_index('batchingmodes_name_key', 'batchingmodes', ['name'], unique=True)
    op.create_table('errorclasses',
    sa.Column('errorclassid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.PrimaryKeyConstraint(u'errorclassid', name=op.f('pk_errorclasses'))
    )
    op.create_index(op.f('ix_errorclasses_name'), 'errorclasses', ['name'], unique=True)
    op.create_table('filehandlers',
    sa.Column('handlerid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.PrimaryKeyConstraint(u'handlerid', name=op.f('pk_filehandlers'))
    )
    op.create_index(op.f('ix_filehandlers_name'), 'filehandlers', ['name'], unique=True)
    op.create_table('jobs',
    sa.Column('jobid', sa.INTEGER(), nullable=False),
    sa.Column('added', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('started', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('completed', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('failed', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.Column('isnew', sa.BOOLEAN(), server_default=sa.text(u'true'), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('pid', sa.INTEGER(), nullable=True),
    sa.PrimaryKeyConstraint(u'jobid', name=op.f('pk_jobs'))
    )
    op.create_table('labelsets',
    sa.Column('labelsetid', sa.INTEGER(), nullable=False),
    sa.Column('created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.PrimaryKeyConstraint(u'labelsetid', name=op.f('pk_labelsets'))
    )
    op.create_table('rates',
    sa.Column('rateid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('centsperutt', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.Column('maxcentsperutt', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.Column('targetaccuracy', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.PrimaryKeyConstraint(u'rateid', name=op.f('pk_rates')),
    sa.CheckConstraint('targetaccuracy>=0 AND targetaccuracy<=1'),
    )
    op.create_index(op.f('ix_rates_name'), 'rates', ['name'], unique=True)
    op.create_table('tagimagepreviews',
    sa.Column('previewid', sa.INTEGER(), nullable=False),
    sa.Column('image', sa.LargeBinary(), nullable=False),
    sa.Column('created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.PrimaryKeyConstraint(u'previewid', name=op.f('pk_tagimagepreviews'))
    )
    op.create_table('tagsets',
    sa.Column('tagsetid', sa.INTEGER(), nullable=False),
    sa.Column('created', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('lastupdated', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.PrimaryKeyConstraint(u'tagsetid', name=op.f('pk_tagsets'))
    )
    op.create_table('taskreporttypes',
    sa.Column('reporttypeid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('isstandard', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.Column('restrictusersallowed', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.PrimaryKeyConstraint(u'reporttypeid', name=op.f('pk_taskreporttypes'))
    )
    op.create_index('taskreporttypes_name_key', 'taskreporttypes', ['name'], unique=True)
    op.create_table('tasktypes',
    sa.Column('tasktypeid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.PrimaryKeyConstraint(u'tasktypeid', name=op.f('pk_tasktypes'))
    )
    op.create_table('worktypes',
    sa.Column('worktypeid', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('modifiestranscription', sa.BOOLEAN(), nullable=False),
    sa.PrimaryKeyConstraint(u'worktypeid', name=op.f('pk_worktypes'))
    )
    op.create_index(op.f('ix_worktypes_name'), 'worktypes', ['name'], unique=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_worktypes_name'), table_name='worktypes')
    op.drop_table('worktypes')
    op.drop_table('tasktypes')
    op.drop_index('taskreporttypes_name_key', table_name='taskreporttypes')
    op.drop_table('taskreporttypes')
    op.drop_table('tagsets')
    op.drop_table('tagimagepreviews')
    op.drop_index(op.f('ix_rates_name'), table_name='rates')
    op.drop_table('rates')
    op.drop_table('labelsets')
    op.drop_table('jobs')
    op.drop_index(op.f('ix_filehandlers_name'), table_name='filehandlers')
    op.drop_table('filehandlers')
    op.drop_index(op.f('ix_errorclasses_name'), table_name='errorclasses')
    op.drop_table('errorclasses')
    op.drop_index('batchingmodes_name_key', table_name='batchingmodes')
    op.drop_table('batchingmodes')
    ### end Alembic commands ###
