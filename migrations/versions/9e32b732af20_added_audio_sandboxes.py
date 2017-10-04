"""added audio sandboxes

Revision ID: 9e32b732af20
Revises: a1258dde113d
Create Date: 2017-09-28 14:05:21.489259

"""

# revision identifiers, used by Alembic.
revision = '9e32b732af20'
down_revision = 'a1258dde113d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table('audio_sandboxes',
    sa.Column('audio_sandbox_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.userid'], ),
    sa.PrimaryKeyConstraint('audio_sandbox_id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('audio_sandbox_files',
    sa.Column('audio_sandbox_file_id', sa.INTEGER(), nullable=False),
    sa.Column('audio_sandbox_id', sa.INTEGER(), nullable=False),
    sa.Column('file_path', sa.TEXT(), nullable=False),
    sa.Column('audio_spec', postgresql.JSONB(), nullable=False),
    sa.Column('audio_data_pointer', postgresql.JSONB(), nullable=False),
    sa.Column('data', postgresql.JSONB(), nullable=True),
    sa.ForeignKeyConstraint(['audio_sandbox_id'], ['audio_sandboxes.audio_sandbox_id'], ),
    sa.PrimaryKeyConstraint('audio_sandbox_file_id')
    )
    op.create_index('audio_sandbox_files_by_audio_sandbox_id', 'audio_sandbox_files', ['audio_sandbox_id'], unique=False)


def downgrade():
    op.drop_table('audio_sandbox_files')
    op.drop_table('audio_sandboxes')

