"""added is_wav flag

Revision ID: 286d5016f800
Revises: 9e32b732af20
Create Date: 2017-10-03 16:12:17.328560

"""

# revision identifiers, used by Alembic.
revision = '286d5016f800'
down_revision = '9e32b732af20'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
	op.add_column(u'audio_sandbox_files', sa.Column('is_wav', sa.BOOLEAN()))
	op.execute("update audio_sandbox_files set is_wav = true")
	op.alter_column("audio_sandbox_files", "is_wav", nullable=False)


def downgrade():
	op.drop_column(u'audio_sandbox_files', 'is_wav')

