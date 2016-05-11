"""Fix duedates for parties

See issue #60; this corrects the duedates on parties already in the database.

Revision ID: 4f5b0f1fc173
Revises: 19693d47a22e
Create Date: 2016-05-11 12:06:17.515644

"""

# revision identifiers, used by Alembic.
revision = '4f5b0f1fc173'
down_revision = '19693d47a22e'
branch_labels = None
depends_on = None

from ironblogger import model
from ironblogger.app import db
from ironblogger.date import to_dbtime, duedate, from_dbtime


def upgrade():
    def _update(dt):
        return to_dbtime(duedate(from_dbtime(dt)))

    for party in model.Party.query.all():
        if party.last_duedate is not None:
            party.last_duedate = _update(party.last_duedate)
        if party.first_duedate is not None:
            party.first_duedate = _update(party.first_duedate)
    db.session.commit()


def downgrade():
    pass
