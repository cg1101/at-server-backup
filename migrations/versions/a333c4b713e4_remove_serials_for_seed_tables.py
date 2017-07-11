"""remove serials for seed tables

Revision ID: a333c4b713e4
Revises: c641c766b860
Create Date: 2017-07-12 09:06:05.005824

"""

# revision identifiers, used by Alembic.
revision = 'a333c4b713e4'
down_revision = 'c641c766b860'
branch_labels = None
depends_on = None

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	
	# audio checking change methods
	op.execute('alter table audio_checking_change_methods alter column change_method_id drop default')
	op.execute('drop sequence audio_checking_change_methods_change_method_id_seq')

	# batching modes
	op.execute('alter table batchingmodes alter column modeid drop default')
	op.execute('drop sequence batchingmodes_modeid_seq')

	# recording platform types
	op.execute('alter table recording_platform_types alter column recording_platform_type_id drop default')
	op.execute('drop sequence recording_platform_types_recording_platform_type_id_seq')

	# task types
	op.execute('alter table tasktypes alter column tasktypeid drop default')
	op.execute('drop sequence tasktypes_tasktypeid_seq')

	# work types
	op.execute('alter table worktypes alter column worktypeid drop default')
	op.execute('drop sequence worktypes_worktypeid_seq')
    

def downgrade():
	conn = context.get_context().connection
	
	# audio checking change methods
	result = conn.execute('select max(change_method_id) from audio_checking_change_methods')
	value = (result.fetchone()[0] or 0) + 1
	op.execute('create sequence audio_checking_change_methods_change_method_id_seq start with {0}'.format(value))
	op.execute("alter table audio_checking_change_methods alter column change_method_id set default nextval('audio_checking_change_methods_change_method_id_seq')")

	# batching modes
	result = conn.execute('select max(modeid) from batchingmodes')
	value = (result.fetchone()[0] or 0) + 1
	op.execute('create sequence batchingmodes_modeid_seq start with {0}'.format(value))
	op.execute("alter table batchingmodes alter column modeid set default nextval('batchingmodes_modeid_seq')")

	# recording platform types
	result = conn.execute('select max(recording_platform_type_id) from recording_platform_types')
	value = (result.fetchone()[0] or 0) + 1
	op.execute('create sequence recording_platform_types_recording_platform_type_id_seq start with {0}'.format(value))
	op.execute("alter table recording_platform_types alter column recording_platform_type_id set default nextval('recording_platform_types_recording_platform_type_id_seq')")

	# task types
	result = conn.execute('select max(tasktypeid) from tasktypes')
	value = (result.fetchone()[0] or 0) + 1
	op.execute('create sequence tasktypes_tasktypeid_seq start with {0}'.format(value))
	op.execute("alter table tasktypes alter column tasktypeid set default nextval('tasktypes_tasktypeid_seq')")

	# work types
	result = conn.execute('select max(worktypeid) from worktypes')
	value = (result.fetchone()[0] or 0) + 1
	op.execute('create sequence worktypes_worktypeid_seq start with {0}'.format(value))
	op.execute("alter table worktypes alter column worktypeid set default nextval('worktypes_worktypeid_seq')")
