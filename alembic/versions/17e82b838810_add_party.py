"""Add party table

Revision ID: 17e82b838810
Revises: 4c3437e18a31
Create Date: 2015-05-28 21:16:56.263701

"""

# revision identifiers, used by Alembic.
revision = '17e82b838810'
down_revision = '4c3437e18a31'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('party',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('spent', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('party')
