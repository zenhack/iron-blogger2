"""Add real name and email fields to blogger

Revision ID: 1b6b1220e217
Revises: 17e82b838810
Create Date: 2015-07-08 20:30:57.950618

"""

# revision identifiers, used by Alembic.
revision = '1b6b1220e217'
down_revision = '17e82b838810'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('blogger', sa.Column('email', sa.String(), nullable=True))
    op.add_column('blogger', sa.Column('real_name', sa.String(), nullable=True))


def downgrade():
    op.drop_column('blogger', 'real_name')
    op.drop_column('blogger', 'email')
