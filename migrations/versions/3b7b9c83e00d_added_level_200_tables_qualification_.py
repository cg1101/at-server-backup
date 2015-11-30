"""added level 200 tables, qualification test related

Revision ID: 3b7b9c83e00d
Revises: 3bd72e01991e
Create Date: 2015-11-30 15:35:20.078291

"""

# revision identifiers, used by Alembic.
revision = '3b7b9c83e00d'
down_revision = '3bd72e01991e'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pools',
    sa.Column('pool_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('meta', sa.TEXT(), nullable=False),
    sa.Column('task_type_id', sa.INTEGER(), nullable=False),
    sa.Column('auto_scoring', sa.BOOLEAN(), server_default=sa.text(u'FALSE'), nullable=False),
    sa.Column('tag_set_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['tag_set_id'], [u'tagsets.tagsetid'], name=op.f('fk_pools_tag_set_id_tagsets')),
    sa.ForeignKeyConstraint(['task_type_id'], [u'tasktypes.tasktypeid'], name=op.f('fk_pools_task_type_id_tasktypes')),
    sa.PrimaryKeyConstraint('pool_id', name=op.f('pk_pools')),
    sa.UniqueConstraint('name', name=op.f('uq_pools_name')),
    schema='q'
    )
    op.create_table('questions',
    sa.Column('question_id', sa.INTEGER(), nullable=False),
    sa.Column('pool_id', sa.INTEGER(), nullable=False),
    sa.Column('respondent_data', sa.TEXT(), server_default=sa.text(u"'{}'::text"), nullable=False),
    sa.Column('scorer_data', sa.TEXT(), server_default=sa.text(u"'{}'::text"), nullable=False),
    sa.Column('auto_scoring', sa.BOOLEAN(), server_default=sa.text(u'FALSE'), nullable=False),
    sa.Column('point', postgresql.DOUBLE_PRECISION(), server_default=sa.text(u'1.0'), nullable=False),
    sa.Column('type', sa.TEXT(), server_default=sa.text(u"'text'::bpchar"), nullable=False),
    sa.ForeignKeyConstraint(['pool_id'], [u'q.pools.pool_id'], name=op.f('fk_questions_pool_id_pools')),
    sa.PrimaryKeyConstraint(u'question_id', name=op.f('pk_questions')),
    schema='q'
    )
    op.create_table('tests',
    sa.Column('test_id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('description', sa.TEXT(), nullable=True),
    sa.Column('instruction_page', sa.TEXT(), nullable=True),
    sa.Column('requirement', sa.TEXT(), server_default=sa.text(u"'{}'::text"), nullable=False),
    sa.Column('time_limit', postgresql.INTERVAL(), server_default=sa.text(u"'02:00:00'::interval"), nullable=False),
    sa.Column('tag_set_id', sa.INTEGER(), nullable=True),
    sa.Column('passing_score', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.Column('test_type', sa.TEXT(), server_default=sa.text(u"'static'::bpchar"), nullable=True),
    sa.Column('size', sa.INTEGER(), nullable=True),
    sa.Column('enabled', sa.BOOLEAN(), server_default=sa.text(u'TRUE'), nullable=False),
    sa.Column('task_type_id', sa.INTEGER(), nullable=False),
    sa.Column('pool_id', sa.INTEGER(), nullable=False),
    sa.Column('message_success', sa.TEXT(), nullable=True),
    sa.Column('message_failure', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['pool_id'], [u'q.pools.pool_id'], name=u'q_tests_poolid_fkey'),
    sa.ForeignKeyConstraint(['tag_set_id'], [u'tagsets.tagsetid'], name=u'q_tests_tagsetid_fkey'),
    sa.ForeignKeyConstraint(['task_type_id'], [u'tasktypes.tasktypeid'], name=u'q_tests__tasktypeid_fkey'),
    sa.PrimaryKeyConstraint(u'test_id', name=op.f('pk_tests')),
    schema='q'
    )
    op.create_table('answer_sheets',
    sa.Column('sheet_id', sa.INTEGER(), nullable=False),
    sa.Column('test_id', sa.INTEGER(), nullable=False),
    sa.Column('userid', sa.INTEGER(), nullable=False),
    sa.Column('n_times', sa.INTEGER(), nullable=False),
    sa.Column('t_started_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('t_expires_by', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('t_expired_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('t_finished_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('score', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.Column('comment', sa.TEXT(), nullable=True),
    sa.Column('more_attempts', sa.BOOLEAN(), server_default=sa.text(u'false'), nullable=False),
    sa.ForeignKeyConstraint(['test_id'], [u'q.tests.test_id'], name=u'q_answer_sheets_testid_fkey'),
    sa.PrimaryKeyConstraint(u'sheet_id', name=op.f('pk_answer_sheets')),
    schema='q'
    )
    op.create_table('sheet_entries',
    sa.Column('sheet_entry_id', sa.INTEGER(), nullable=False),
    sa.Column('sheet_id', sa.INTEGER(), nullable=False),
    sa.Column('index', sa.INTEGER(), nullable=False),
    sa.Column('question_id', sa.INTEGER(), nullable=False),
    sa.Column('answer_id', sa.INTEGER(), nullable=True),
    sa.Column('marking_id', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], [u'q.questions.question_id'], name=op.f('fk_sheet_entries_question_id_questions')),
    sa.ForeignKeyConstraint(['sheet_id'], [u'q.answer_sheets.sheet_id'], name=op.f('fk_sheet_entries_sheet_id_answer_sheets')),
    sa.PrimaryKeyConstraint(u'sheet_entry_id', name=op.f('pk_sheet_entries')),
    schema='q'
    )
    op.create_table('answers',
    sa.Column('answer_id', sa.INTEGER(), nullable=False),
    sa.Column('sheet_entry_id', sa.INTEGER(), nullable=False),
    sa.Column('answer', sa.TEXT(), nullable=False),
    sa.Column('t_created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.ForeignKeyConstraint(['sheet_entry_id'], [u'q.sheet_entries.sheet_entry_id'], name=op.f('fk_answers_sheet_entry_id_sheet_entries')),
    sa.PrimaryKeyConstraint(u'answer_id', name=op.f('pk_answers')),
    schema='q'
    )
    op.create_index('answer_by_sheet_entry_id', 'answers', ['sheet_entry_id'], unique=False, schema='q')
    op.create_table('markings',
    sa.Column('marking_id', sa.INTEGER(), nullable=False),
    sa.Column('sheet_entry_id', sa.INTEGER(), nullable=False),
    sa.Column('t_created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text(u'now()'), nullable=False),
    sa.Column('scorer_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('score', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.Column('comment', sa.TEXT(), nullable=True),
    sa.ForeignKeyConstraint(['scorer_id'], [u'users.userid'], name=u'q_markings_userid_fkey'),
    sa.ForeignKeyConstraint(['sheet_entry_id'], [u'q.sheet_entries.sheet_entry_id'], name=op.f('fk_markings_sheet_entry_id_sheet_entries')),
    sa.PrimaryKeyConstraint(u'marking_id', u'scorer_id', name=op.f('pk_markings')),
    schema='q'
    )
    op.create_index('marking_by_sheet_entry_id', 'markings', ['sheet_entry_id'], unique=False, schema='q')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('marking_by_sheet_entry_id', table_name='markings', schema='q')
    op.drop_table('markings', schema='q')
    op.drop_index('answer_by_sheet_entry_id', table_name='answers', schema='q')
    op.drop_table('answers', schema='q')
    op.drop_table('sheet_entries', schema='q')
    op.drop_table('answer_sheets', schema='q')
    op.drop_table('tests', schema='q')
    op.drop_table('questions', schema='q')
    op.drop_table('pools', schema='q')
    ### end Alembic commands ###
