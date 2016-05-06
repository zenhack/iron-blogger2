from datetime import datetime
import unittest
import pytest
from .util import fresh_context
from .util.example_data import databases as example_databases

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

    def test_enter_dst(self):
        # This is a regression test for bug #51, fixed in commit
        # 90d25c748fe74eb66630c867c956b88afbf2c6ba.
        # For reference, DST for 2016 in Boston ends Sunday November 6th.

        posts = [
            Post(
                title="DST: the end is neigh",
                timestamp=datetime(2016, 11, 4),
                summary="This is going to cause so many bugs.",
                page_url="http://example.com/alice/dst-the-end-is-neigh.html",
            ),
            Post(
                title="DST is over!",
                timestamp=datetime(2016, 11, 8),
                summary="Oh wow, nothing broke. that's a relief",
                page_url="http://example.com/alice/dst-is-over.html",
            ),
            Post(
                title="Maybe I'll push my luck...",
                timestamp=datetime(2016, 11, 9),
                summary="by posting twice right after the changeover.",
                page_url="http://example.com/alice/push-my-luck.html",
            )
        ]

        db.session.add(
            Blogger(name='Alice',
                    start_date=datetime(2016, 11, 3),
                    blogs=[
                        Blog(
                            title="Timezones are Horrible",
                            page_url="http://example.com/alice/blog.html",
                            feed_url="http://example.com/alice/rss.xml",
                            posts=posts
                        )
                    ]))

        end_date = datetime(2016, 11, 14)
        tasks.assign_rounds(until=end_date)
        self.verify_assignment(datetime(2016, 11, 5), "neigh", 0)
        self.verify_assignment(datetime(2016, 11, 10), "over",  0)
        assert posts[2].counts_for is None
