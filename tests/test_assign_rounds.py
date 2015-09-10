from datetime import datetime
import unittest
import pytest
from tests.util import fresh_context, example_databases

from ironblogger.model import db, Blogger, Blog, Post
from ironblogger.app import app
from ironblogger.date import duedate
from ironblogger import tasks

fresh_context = pytest.yield_fixture(autouse=True)(fresh_context)


class Test_assign_rounds(unittest.TestCase):

    def _get_week(self, when):
        return db.session.query(Post)\
            .filter_by(counts_for=duedate(when)).first()

    def verify_assignment(self, when, title_part, late):
        post = self._get_week(when)
        assert title_part in post.title
        assert post.rounds_late() == late

    def test_01(self):
        # During a 5-week period, alice:
        #
        # * Posts on time in the first week
        # * Misses week 2
        # * Posts twice in week 3
        # * Misses weeks 4 and 5
        db.session.add(example_databases[0]())
        end_date = datetime(2015, 4, 28)
        tasks.assign_rounds(until=end_date)
        self.verify_assignment(datetime(2015, 4,  1), "BREAKING:",       0)
        self.verify_assignment(datetime(2015, 4, 15), "Security Breach", 0)
        self.verify_assignment(datetime(2015, 4,  8), "Javascript",      1)
        assert self._get_week(datetime(2015, 4, 22)) is None

        # Just make sure this doesn't explode:
        tasks.assign_rounds()

    def test_02(self):
        # During a 4 week-period, bob:
        #
        # * Posts once in round 1
        # * Twice in round 2
        # * Once in round 3
        # * Misses round 4
        db.session.add(example_databases[1]())
        end_date = datetime(2015, 4, 21)
        tasks.assign_rounds(until=end_date)
        self.verify_assignment(datetime(2015, 4,  1), "Rivest",         0)
        self.verify_assignment(datetime(2015, 4,  8), "hash functions", 0)
        self.verify_assignment(datetime(2015, 4, 15), "depression",     0)
        assert self._get_week(datetime(2015, 4, 22)) is None
        extra_post = db.session.query(Post).filter_by(timestamp=datetime(2015, 4, 9)).one()
        assert extra_post.rounds_late() is None

        # Just make sure this doesn't explode:
        tasks.assign_rounds()
