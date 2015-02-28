"""add_caching_info

Revision ID: 4e82f996fc77
Revises: 1c24cd433332
Create Date: 2015-02-27 21:41:25.780039

"""

# revision identifiers, used by Alembic.
revision = '4e82f996fc77'
down_revision = '1c24cd433332'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('blog', sa.Column('etag', sa.String(), nullable=True))
    op.add_column('blog', sa.Column('modified', sa.String(), nullable=True))


def downgrade():
    op.drop_column('blog', 'modified')
    op.drop_column('blog', 'etag')
