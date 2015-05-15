"""add user and payment tables

Revision ID: 4c3437e18a31
Revises: 183d203407a6
Create Date: 2015-05-14 20:37:09.960093

"""

# revision identifiers, used by Alembic.
revision = '4c3437e18a31'
down_revision = '183d203407a6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('blogger_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['blogger_id'], ['blogger.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=True),
    sa.Column('blogger_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['blogger_id'], ['blogger.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('blogger_id'),
    sa.UniqueConstraint('name')
    )


def downgrade():
    op.drop_table('user')
    op.drop_table('payment')
