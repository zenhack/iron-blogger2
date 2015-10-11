"""Add first/last duedates for parties.

Revision ID: 1211671dc1c3
Revises: 191ea9ef2e8c
Create Date: 2015-10-10 23:10:03.428791

"""

# revision identifiers, used by Alembic.
revision = '1211671dc1c3'
down_revision = '191ea9ef2e8c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('party', sa.Column('first_duedate', sa.DateTime()))
    op.add_column('party', sa.Column('last_duedate', sa.DateTime()))
    op.create_unique_constraint(None, 'party', ['last_duedate'])
    op.create_unique_constraint(None, 'party', ['first_duedate'])


def downgrade():
    op.drop_constraint(None, 'party', type_='unique')
    op.drop_constraint(None, 'party', type_='unique')
    op.drop_column('party', 'last_duedate')
    op.drop_column('party', 'first_duedate')
