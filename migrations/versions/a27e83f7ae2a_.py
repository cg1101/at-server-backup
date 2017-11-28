"""empty message

Revision ID: a27e83f7ae2a
Revises: 717e10c4d492
Create Date: 2017-11-28 11:18:06.203174

"""

# revision identifiers, used by Alembic.
revision = 'a27e83f7ae2a'
down_revision = '717e10c4d492'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('phones',
    sa.Column('key', sa.TEXT(), nullable=False),
    sa.Column('type', sa.TEXT(), nullable=False),
    sa.Column('label', sa.TEXT(), nullable=True),
    sa.Column('ipa_number', sa.INTEGER(), nullable=True),
    sa.Column('x_sampa', sa.TEXT(), nullable=True),
    sa.Column('appen_sampa', sa.TEXT(), nullable=True),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('ph_consonants',
    sa.Column('key', sa.TEXT(), nullable=False),
    sa.Column('sub_type', sa.TEXT(), nullable=False),
    sa.Column('voicing', sa.TEXT(), nullable=False),
    sa.Column('place', sa.TEXT(), nullable=False),
    sa.Column('manner', sa.TEXT(), nullable=False),
    sa.Column('central_lateral', sa.TEXT(), nullable=False),
    sa.Column('coarticulation', sa.TEXT(), nullable=False),
    sa.Column('second_place', sa.TEXT(), nullable=False),
    sa.Column('diacritic', sa.TEXT(), nullable=False),
    sa.CheckConstraint(u"manner=ANY(ARRAY['nasal','plosive','ejective','implosive','click','fricative','affricate','approximant','tap','flap','trill'])"),
    sa.CheckConstraint(u"place=ANY(ARRAY['bilabial','labiodental','dental','alveolar','alveolo-palatal','postalveolar','retroflex','palatal','velar','uvular','pharyngeal','epiglottal','glottal'])"),
    sa.CheckConstraint(u"voicing=ANY(ARRAY['voiceless', 'voiced'])"),
    sa.ForeignKeyConstraint(['key'], ['phones.key'], ),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('ph_diacritics',
    sa.Column('key', sa.TEXT(), nullable=False),
    sa.Column('sub_type', sa.TEXT(), nullable=False),
    sa.ForeignKeyConstraint(['key'], ['phones.key'], ),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('ph_suprasegmentals',
    sa.Column('key', sa.TEXT(), nullable=False),
    sa.Column('sub_type', sa.TEXT(), nullable=False),
    sa.ForeignKeyConstraint(['key'], ['phones.key'], ),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('ph_vowels',
    sa.Column('key', sa.TEXT(), nullable=False),
    sa.Column('sub_type', sa.TEXT(), nullable=False),
    sa.Column('height', sa.TEXT(), nullable=True),
    sa.Column('backness', sa.TEXT(), nullable=True),
    sa.Column('rounding', sa.TEXT(), nullable=True),
    sa.Column('nasal', sa.TEXT(), nullable=True),
    sa.Column('length', sa.TEXT(), nullable=True),
    sa.Column('movement', sa.TEXT(), nullable=True),
    sa.CheckConstraint(u"backness=ANY(ARRAY['front', 'near-front', 'central', 'near-back', 'back'])"),
    sa.CheckConstraint(u"height=ANY(ARRAY['close', 'near-close', 'close-mid', 'mid', 'open-mid', 'near-open', 'open'])"),
    sa.CheckConstraint(u"rounding=ANY(ARRAY['unrounded', 'rounded'])"),
    sa.CheckConstraint(u"sub_type=ANY(ARRAY['monophthong', 'diphthong', 'triphthong'])"),
    sa.ForeignKeyConstraint(['key'], ['phones.key'], ),
    sa.PrimaryKeyConstraint('key')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ph_vowels')
    op.drop_table('ph_suprasegmentals')
    op.drop_table('ph_diacritics')
    op.drop_table('ph_consonants')
    op.drop_table('phones')
    ### end Alembic commands ###