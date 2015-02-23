"""Remove max length from strings.

This is deemed undesirable since:

* In most cases, there isn't a "natural" length.
* Neither sqlite nor postgres require this.
* MySQL silently truncates values that are too long, which is dangerous.

We don't need MySQL support, and prefer a correct implementation over one that
is portable to MySQL.

Revision ID: 1c24cd433332
Revises:
Create Date: 2015-02-22 20:19:06.813882

"""

# revision identifiers, used by Alembic.
revision = '1c24cd433332'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('blogger', 'name', type_=sa.String)

    op.alter_column('blog', 'title', type_=sa.String)
    op.alter_column('blog', 'page_url', type_=sa.String)
    op.alter_column('blog', 'feed_url', type_=sa.String)

    op.alter_column('post', 'title', type_=sa.String)
    op.alter_column('post', 'page_url', type_=sa.String)


def downgrade():
    op.alter_column('blogger', 'name', type_=sa.String(255))

    op.alter_column('blog', 'title', type_=sa.String(255))
    op.alter_column('blog', 'page_url', type_=sa.String(255))
    op.alter_column('blog', 'feed_url', type_=sa.String(255))

    op.alter_column('post', 'title', type_=sa.String(255))
    op.alter_column('post', 'page_url', type_=sa.String(255))
