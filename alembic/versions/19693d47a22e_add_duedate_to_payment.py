"""Add duedate to payment

Revision ID: 19693d47a22e
Revises: 1211671dc1c3
Create Date: 2015-10-11 00:32:32.520909

"""

# revision identifiers, used by Alembic.
revision = '19693d47a22e'
down_revision = '1211671dc1c3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('payment', sa.Column('duedate', sa.DateTime(), nullable=False))


def downgrade():
    op.drop_column('payment', 'duedate')
