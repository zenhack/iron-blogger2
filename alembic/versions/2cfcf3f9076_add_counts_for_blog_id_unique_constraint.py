"""add-counts_for-blog_id-unique-constraint

Revision ID: 2cfcf3f9076
Revises: 1b6b1220e217
Create Date: 2015-07-18 00:02:11.146764

"""

# revision identifiers, used by Alembic.
revision = '2cfcf3f9076'
down_revision = '1b6b1220e217'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.create_unique_constraint(None, 'post', ['counts_for', 'blog_id'])


def downgrade():
    op.drop_constraint(None, 'post', type_='unique')
