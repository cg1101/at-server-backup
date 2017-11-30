"""added audio uploads table

Revision ID: 130090387260
Revises: a27e83f7ae2a
Create Date: 2017-11-27 14:01:25.381435

"""

# revision identifiers, used by Alembic.
revision = '130090387260'
down_revision = 'a27e83f7ae2a'
branch_labels = None
depends_on = None

import datetime
import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.create_table('audio_uploads',
	sa.Column('audio_upload_id', sa.INTEGER(), nullable=False),
	sa.Column('task_id', sa.INTEGER(), nullable=False),
	sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
	sa.Column('data', postgresql.JSONB(), nullable=False),
	sa.Column('hidden', sa.BOOLEAN(), nullable=False),
	sa.ForeignKeyConstraint(['task_id'], ['tasks.taskid'], ),
	sa.PrimaryKeyConstraint('audio_upload_id')
	)
	op.create_index('audio_uploads_by_task_id', 'audio_uploads', ['task_id'], unique=False)

	conn = op.get_bind()
	res = conn.execute("select taskid, audio_uploads from tasks where audio_uploads is not null")
	results = res.fetchall()

	for task_id, data in results:

		if isinstance(data, list) and data:
			for entry in data:
				created_at = datetime.datetime.utcfromtimestamp(entry["info"]["finishedAt"])
				conn.execute(
					"insert into audio_uploads (task_id, created_at, data, hidden) values (%(task_id)s, %(created_at)s, %(data)s, false)",
					task_id=task_id,
					created_at=created_at,
					data=json.dumps(entry),
				)

	op.drop_column(u'tasks', 'audio_uploads')


def downgrade():
	op.add_column(u'tasks', sa.Column('audio_uploads', postgresql.JSONB(), autoincrement=False, nullable=True))
	op.drop_table('audio_uploads')
