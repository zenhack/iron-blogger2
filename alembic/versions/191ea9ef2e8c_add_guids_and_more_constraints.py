"""Add guids and more constraints

Revision ID: 191ea9ef2e8c
Revises: 2cfcf3f9076
Create Date: 2015-10-10 15:37:56.459964

"""

# revision identifiers, used by Alembic.
revision = '191ea9ef2e8c'
down_revision = '2cfcf3f9076'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('post', sa.Column('guid', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'post', ['blog_id', 'page_url'])
    op.create_unique_constraint(None, 'post', ['blog_id', 'guid'])


def downgrade():
    op.drop_constraint(None, 'post', type_='unique')
    op.drop_constraint(None, 'post', type_='unique')
    op.drop_column('post', 'guid')
