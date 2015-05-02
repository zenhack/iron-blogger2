"""Add counts_for field to post

Revision ID: 183d203407a6
Revises: 4e82f996fc77
Create Date: 2015-05-02 15:12:44.273333

"""

# revision identifiers, used by Alembic.
revision = '183d203407a6'
down_revision = '4e82f996fc77'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('post', sa.Column('counts_for', sa.DateTime))


def downgrade():
    op.drop_column('post', 'counts_for')
