import pytest
from tests.util import fresh_context
from datetime import date
from ironblogger.model import db, Blogger


fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)


def test_missed_posts():
    blogger = Blogger('alice', date(2015, 1, 18))
    db.session.add(blogger)
    db.session.commit()
    assert blogger.missed_posts(until=date(2015, 1, 25)) == 1
    assert blogger.missed_posts(since=date(2015, 1, 25), until=date(2015, 1, 25)) == 0
