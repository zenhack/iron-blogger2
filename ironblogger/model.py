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
from datetime import date
import time
import logging

from flask.ext.sqlalchemy import SQLAlchemy
import feedparser
import jinja2

VCHAR_DEFAULT = 255  # Default length of string/varchar columns.
                     # This might not actually be enough for some urls.

db = SQLAlchemy()


class MalformedPostError(Exception):
    """Raised when parsing a post fails."""


class Blogger(db.Model):
    """An Iron Blogger participant."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(VCHAR_DEFAULT), nullable=False, unique=True)
    start_date = db.Column(db.Date, nullable=False)

    def __init__(self, name, start_date, blogs=None):
        self.name = name
        self.start_date = start_date
        if blogs is not None:
            self.blogs = blogs

    def compute_debt(self, since=None, until=None):
        if since is None:
            since = self.start_date
        if until is None:
            until = date.today()
        posts = db.session.query(Post) \
                .filter_by(since < Post.date < until) \
                .filter_by(Post.blog.blogger == self) \
                .order_by(Post.date.desc()).all()


class Blog(db.Model):
    """A blog. bloggers may have more than one of these."""
    id = db.Column(db.Integer, primary_key=True)
    blogger_id = db.Column(db.Integer, db.ForeignKey('blogger.id'),
                           nullable=False)
    blogger = db.relationship('Blogger', backref=db.backref('blogs'))
    title = db.Column(db.String(VCHAR_DEFAULT), nullable=False)

    # Human readable webpage:
    page_url = db.Column(db.String(VCHAR_DEFAULT), nullable=False)

    # Atom/RSS feed:
    feed_url = db.Column(db.String(VCHAR_DEFAULT), nullable=False)

    def __init__(self, title, page_url, feed_url, blogger=None):
        self.title = title
        self.page_url = page_url
        self.feed_url = feed_url
        if blogger is not None:
            self.blogger = blogger

    def sync_posts(self):
        logging.info('Syncing posts for blog %r by %r',
                     self.title,
                     self.blogger.name)
        last_post = db.session.query(Post)\
            .filter_by(blog=self)\
            .order_by(Post.date.desc()).first()
        feed = feedparser.parse(self.feed_url)
        feed_posts = map(Post.from_feed_entry, feed.entries)

        # The loop below assumes our feed entries are sorted by date, newest
        # first. This ensures just that:
        feed_posts = sorted([(post.date, post) for post in feed_posts])
        feed_posts.reverse()
        feed_posts = [post for (_date, post) in feed_posts]

        for post in feed_posts:
            # Check if the post is already in the db:
            if last_post is not None:
                if post.date < last_post.date:
                    # We can stop storing posts when we get to one that's older
                    # than one we already have. Note that we can't do less than
                    # or equal here, since someone might post more than one
                    # post in a day.
                    break
                if post.date == last_post.date and post.title == last_post.title:
                    # If a post has the same date as one already in the db (on
                    # the same blog), we use the title as an identifier.
                    break

            post.blog = self
            db.session.add(post)
            logging.info('Added new post %r', post.page_url)
        db.session.commit()


class Post(db.Model):
    """A blog post."""
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(VCHAR_DEFAULT), nullable=False)

    # The *sanitized* description/summary field from the feed entry. This will
    # be copied directly to the generated html, so sanitization is critical.
    summary = db.Column(db.Text, nullable=False)

    # URL for the HTML version of the post.
    page_url = db.Column(db.String(VCHAR_DEFAULT), nullable=False)
    blog = db.relationship('Blog', backref=db.backref('posts'))

    @staticmethod
    def _get_pub_date(feed_entry):
        """Return a datetime.date object for the post's publication date.

        ``feed_entry`` should be a post object as returned by
        ``feedparser.parse``.

        If the post does not have a publication date, raise a
        ``MalformedPostError``.
        """
        for key in 'published', 'created', 'updated':
            key += '_parsed'
            if key in feed_entry and feed_entry[key] is not None:
                return date.fromtimestamp(time.mktime(feed_entry[key]))
        raise MalformedPostError("No valid publication date in post: %r" %
                                 feed_entry)

    def due(self):
        """Return the date for which this post counted."""

        # There has got to be a better way to do this.
        one_day = date(2015, 1, 2) - date(2015, 1, 1)
        sunday = 6

        weekday = self.date.weekday()
        return self.date + (one_day * (sunday - weekday))


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
        post.date = Post._get_pub_date(entry)
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
