# Copyright 2014-2015 Ian Denhardt <ian@zenhack.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>
from datetime import datetime, timedelta
import time
import logging

from flask.ext.sqlalchemy import SQLAlchemy
import feedparser
import jinja2

import ironblogger.date
from ironblogger.date import duedate, ROUND_LEN

DEBT_PER_POST = 5
LATE_PENALTY = 1

feedparser.USER_AGENT = \
        'IronBlogger/git ' + \
        '+https://github.com/zenhack/iron-blogger2 ' + \
        feedparser.USER_AGENT


db = SQLAlchemy()

class MalformedPostError(Exception):
    """Raised when parsing a post fails."""


class Blogger(db.Model):
    """An Iron Blogger participant."""
    id         = db.Column(db.Integer,  primary_key=True)
    name       = db.Column(db.String,   nullable=False, unique=True)
    start_date = db.Column(db.DateTime, nullable=False)

    def __init__(self, name, start_date, blogs=None):
        self.name = name
        self.start_date = start_date
        if blogs is not None:
            self.blogs = blogs

    def create_rounds(self, until=None):
        """Create any missing BloggerRounds between self.start_date and duedate(until).

        If until is None, it defaults to datetime.now().
        """
        if until is None:
            until = datetime.now()

        round = db.session.query(BloggerRound)\
            .filter_by(blogger=self)\
            .order_by(BloggerRound.due.desc())\
            .first()

        if round is None:
            round = BloggerRound(blogger=self,
                                 due=duedate(self.start_date))
            db.session.add(round)

        while round.due < duedate(until):
            round = BloggerRound(blogger=self,
                                 due=duedate(round.due + ROUND_LEN))
            db.session.add(round)

    def assign_posts(self, since=None, until=None):
        """Assign the blogger's posts to rounds."""

        if until is None:
            until = datetime.now()
        if since is None:
            since = duedate(self.start_date)
        since = min(since, self.start_date)  # If the caller specifies to early a since...

        # Get all of the rounds with no post, which are recent enough for the
        # blogger to get credit:
        rounds = db.session.query(BloggerRound)\
            .filter(BloggerRound.post == None,
                    BloggerRound.due >= since,
                    BloggerRound.blogger_id == self.id)\
            .order_by(BloggerRound.due.desc()).all()

        for round in rounds:
            # Get the earliest post that could count towards this round. For a
            # post to be eligible, it must:
            #
            # * Not already have a round assigned
            # * Be posted sometime after the round begins
            # * Be posted recently enough to get *some* credit
            # * Be written by the correct blogger (duh, but important)
            last_eligible_date = round.due + ROUND_LEN * (DEBT_PER_POST / LATE_PENALTY)
            round.post = db.session.query(Post)\
                .filter(Post.round == None,
                        Post.timestamp > round.due - ROUND_LEN,
                        Post.timestamp < last_eligible_date,
                        Post.blog_id == Blog.id,
                        Blog.blogger_id == round.blogger_id)\
                .order_by(Post.timestamp).first()  # conveniently, this returns None if there's no
                                                   # post.

    def missed_posts(self, since=None, until=None):
        """Return the number of posts the blogger has missed.

        If since is not None, the result will count starting from since.
        Otherwise, it will count starting from the blogger's start_date.

        If until is not None, the result will be the number of missed posts up
        to until. Otherwise, it will be the number of missed posts up to the
        present.
        """
        if since is None:
            since = self.start_date
        if until is None:
            until = datetime.now()

        first_duedate = duedate(since)
        last_duedate = duedate(until) - ROUND_LEN

        posts = db.session.query(Post).filter(
            (first_duedate - ROUND_LEN) < Post.timestamp,
            Post.timestamp < last_duedate,
            Post.blog_id == Blog.id,
            Blog.blogger_id == Blogger.id,
            Blogger.id == self.id,
        ).all()

        met = set()
        for post in posts:
            met.add(duedate(post.timestamp))
        num_duedates = (last_duedate - first_duedate + ROUND_LEN).days / 7
        return num_duedates - len(met)


class BloggerRound(db.Model):
    """A BloggerRound is a record of a blogger's status in a given round.

    You might think of this as a joining table, except that, at present,
    there's nothing we need to store in a "rounds" table, so the other
    table doesn't exist yet.
    """
    id         = db.Column(db.Integer,  primary_key=True)
    blogger_id = db.Column(db.Integer,  db.ForeignKey('blogger.id'), nullable=False)
    post_id    = db.Column(db.Integer,  db.ForeignKey('post.id'),    unique=True)
    due        = db.Column(db.DateTime, nullable=False)
    paid       = db.Column(db.Integer,  nullable=False, default=0)  # Amount paid in USD
    forgiven   = db.Column(db.Integer,  nullable=False, default=0)  # Amount "forgiven" by the admin, in USD.

    blogger = db.relationship('Blogger', backref=db.backref('rounds'))
    post    = db.relationship('Post', backref=db.backref('round', uselist=False))

    def rounds_late(self):
        # timedelta doesn't have a divide operator, so we convert to actual
        # numbers first:
        seconds_late = (duedate(self.post.timestamp) - self.due).total_seconds()
        round_seconds = ROUND_LEN.total_seconds()
        return int(seconds_late/round_seconds)

    def owed(self):
        if not self.post:
            return DEBT_PER_POST
        else:
            penalty = self.rounds_late() * LATE_PENALTY
            return min(DEBT_PER_POST, penalty) - self.paid - self.forgiven

    def sanity_check(self):
        assert self.owed() >= 0
        assert self.owed() <= DEBT_PER_POST


class Blog(db.Model):
    """A blog. bloggers may have more than one of these."""
    id         = db.Column(db.Integer, primary_key=True)
    blogger_id = db.Column(db.Integer, db.ForeignKey('blogger.id'), nullable=False)
    title      = db.Column(db.String, nullable=False)
    page_url   = db.Column(db.String, nullable=False)  # Human readable webpage
    feed_url   = db.Column(db.String, nullable=False)  # Atom/RSS feed
    # Metadata for caching:
    etag       = db.Column(db.String)  # see: https://pythonhosted.org/feedparser/http-etag.html
    modified   = db.Column(db.String)  # We don't bother parsing this; it's only for the server's
                                       # Benefit.

    blogger = db.relationship('Blogger', backref=db.backref('blogs'))

    def sync_posts(self):
        logging.info('Syncing posts for blog %r by %r',
                     self.title,
                     self.blogger.name)
        last_post = db.session.query(Post)\
            .filter_by(blog=self)\
            .order_by(Post.timestamp.desc()).first()
        feed = feedparser.parse(self.feed_url,
                                etag=self.etag,
                                modified=self.modified)
        if hasattr(feed, 'status') and feed.status == 304:
            logging.info('Feed for blog %r (by %r) was not modified.',
                         self.title,
                         self.blogger.name)

        feed_posts = map(Post.from_feed_entry, feed.entries)

        # The loop below assumes our feed entries are sorted by date, newest
        # first. This ensures just that:
        feed_posts = sorted([(post.timestamp, post) for post in feed_posts])
        feed_posts.reverse()
        feed_posts = [post for (_date, post) in feed_posts]

        for post in feed_posts:
            # Check if the post is already in the db:
            if last_post is not None:
                if post.timestamp < last_post.timestamp:
                    # We can stop storing posts when we get to one that's older
                    # than one we already have. Note that we can't do less than
                    # or equal here, since someone might post more than one
                    # post in a day.
                    break
                if post.timestamp == last_post.timestamp and post.title == last_post.title:
                    # If a post has the same date as one already in the db (on
                    # the same blog), we use the title as an identifier.
                    break

            post.blog = self
            db.session.add(post)
            logging.info('Added new post %r', post.page_url)
        self._update_caching_info(feed)
        db.session.commit()


    def _update_caching_info(self, feed):
        if hasattr(feed, 'etag'):
            self.etag = feed.etag
        if hasattr(feed, 'modified'):
            self.modified = feed.modified


class Post(db.Model):
    """A blog post."""
    id        = db.Column(db.Integer,  primary_key=True)
    blog_id   = db.Column(db.Integer,  db.ForeignKey('blog.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    title     = db.Column(db.String,   nullable=False)
    # The *sanitized* description/summary field from the feed entry. This will
    # be copied directly to the generated html, so sanitization is critical:
    summary   = db.Column(db.Text,     nullable=False)
    page_url  = db.Column(db.String,   nullable=False)

    blog = db.relationship('Blog', backref=db.backref('posts'))

    @staticmethod
    def _get_pub_date(feed_entry):
        """Return a datetime.datetime object for the post's publication date.

        ``feed_entry`` should be a post object as returned by
        ``feedparser.parse``.

        If the post does not have a publication date, raise a
        ``MalformedPostError``.
        """
        for key in 'published', 'created', 'updated':
            key += '_parsed'
            if key in feed_entry and feed_entry[key] is not None:
                return datetime.fromtimestamp(time.mktime(feed_entry[key]))
        raise MalformedPostError("No valid publication date in post: %r" %
                                 feed_entry)


    @staticmethod
    def from_feed_entry(entry):
        """Read and construct Post object from ``entry``.

        ``entry`` should be a post object as returned by ``feedparser.parse``.

        If the post is invalid, raise a ``MalformedPostError`.

        This leaves the `blog` field emtpy; this must be filled in before the
        post is added to the database.
        """
        for field in 'title', 'summary', 'link':
            if field not in entry:
                raise MalformedPostError("Post has no %s: %r" % (field, entry))
        post = Post()
        post.timestamp = Post._get_pub_date(entry)
        post.title = entry['title']
        post.summary = entry['summary']

        # The summary detail attribute lets us find the mime type of the
        # summary. feedparser doesn't escape it if it's text/plain, so we need
        # to do it ourselves. Unfortunately, there's a bug (likely #412) in
        # feedparser, and sometimes this attribute is unavailable. If it's
        # there, great, use it. Otherwise, we'll just assume it's html, and
        # sanitize it ourselves.
        if hasattr(entry, 'summary_detail'):
            mimetype = entry.summary_detail.type
        else:
            mimetype = 'application/xhtml'
            # Sanitize the html; who knows what feedparser did or didn't do.
            # XXX: _sanitizeHTML is a private function to the feedparser
            # library! unfortunately, we don't have many better options. This
            # statement is the reason the version number for the feedparser
            # dependency is fixed at 5.1.3; any alternate version will need to
            # be vetted carefully, as by doing this we lose any api stability
            # guarantees.
            post.summary = unicode(feedparser._sanitizeHTML(
                # _sanitizeHTML expects an encoding, so rather than do more
                # guesswork than we alredy have...
                post.summary.encode('utf-8'),
                'utf-8',
                # _sanitizeHTML is only ever called within the library with
                # this value:
                u'text/html',
            ), 'utf-8')

        if mimetype == 'text/plain':
            # feedparser doesn't sanitize the summary if it's plain text, so we
            # need to do it manually. We're using jijna2's autoscape feature
            # for this, which feels like a bit of a hack to me (Ian), but it
            # works -- there's probably a cleaner way to do this.
            tmpl = jinja2.Template('{{ text }}', autoescape=True)
            post.summary = tmpl.render(text=post.summary)
        post.page_url = entry['link']

        return post

    def rssdate(self):
        return ironblogger.date.rssdate(self.timestamp)
