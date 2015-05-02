from datetime import datetime
import unittest

from ironblogger.model import db, Blogger, Blog, BloggerRound, Post
from ironblogger.app import app
from ironblogger.wsgi import setup
from ironblogger.date import duedate
from ironblogger import tasks


class Test_assign_posts(unittest.TestCase):

    def setUp(self):
        self.ctx = app.test_request_context()
        self.ctx.push()
        setup({
            'region'  : 'Boston',
            'timezone': '-0500',
            'language': 'en-us',
            'db_uri'  : 'sqlite:///:memory:',
        })
        db.create_all()

        # During a 5-week period, alice:
        #
        # * Posts on time in the first week
        # * Misses week 2
        # * Posts twice in week 3
        # * Misses weeks 4 and 5
        alice = Blogger(name='Alice',
                        start_date=datetime(2015, 4, 1),
                        blogs=[
                            Blog(title='Fun with crypto',
                                page_url='http://example.com/alice/blog.html',
                                feed_url='http://example.com/alice/rss.xml',
                                posts=[
                                    Post(timestamp=datetime(2015, 4, 1),
                                        title="BREAKING: P = NP; Asymmetric crypto broken forever :(",
                                        summary="The title says it all. There are many other "
                                                "implications of this, but given the topic of...",
                                        page_url='http://example.com/alice/april-fools-pnp.html',
                                        ),
                                    Post(timestamp=datetime(2015, 4, 15),
                                        title="Security Breach",
                                        summary="Sorry I didn't post last week. There was a security "
                                                "breach at work, and I was busy dealing with...",
                                        page_url='http://example.com/alice/security-breach.html',
                                        ),
                                    Post(timestamp=datetime(2015, 4, 16),
                                        title="Javascript and timing attacks",
                                        summary="Owing to it being the only thing available in the "
                                                "browser, people are doing more and more with Javascript...",
                                        page_url='http:///example.com/alice/javascript-timing-attacks.html',
                                        ),
                                    ]
                                )])
        db.session.add(alice)
        self.alice = alice
        self.end_date = datetime(2015, 4, 28)

    def tearDown(self):
        db.drop_all()
        self.ctx.pop()

    def _get_week(self, when):
        return db.session.query(BloggerRound)\
            .filter_by(due=duedate(when)).one()

    def verify_assignments(self):
        assert "BREAKING:" in self._get_week(datetime(2015, 4, 1)).post.title
        assert "Security Breach" == self._get_week(datetime(2015, 4, 15)).post.title
        assert "Javascript" in self._get_week(datetime(2015, 4, 8)).post.title
        assert self._get_week(datetime(2015, 4, 22)).post is None

    def test_blogger_method(self):
        """Test the assign_posts method of the Blogger class"""
        self.alice.create_rounds(self.end_date)
        self.alice.assign_posts(until=self.end_date)
        self.verify_assignments()

        # Just make sure this doesn't explode:
        self.alice.assign_posts()

    def test_tasks_function(self):
        tasks.create_rounds(self.end_date)
        tasks.assign_posts(until=self.end_date)
        self.verify_assignments()

        tasks.assign_posts()
