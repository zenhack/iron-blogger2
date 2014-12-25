#!/usr/bin/env python
# Copyright 2014 Ian Denhardt <ian@zenhack.net>
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

from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
import feedparser

VCHAR_DEFAULT = 255  # Default length of string/varchar columns.
                     # This might not actually be enough for some urls.

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iron-blogger.db'
db = SQLAlchemy(app)


class MalformedPostError(Exception):
    """Raised when parsing a post fails."""


class Blogger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(VCHAR_DEFAULT), nullable=False, unique=True)
    start_date = db.Column(db.Date, nullable=False)

    def __init__(self, name, start_date, blogs=None):
        self.name = name
        self.start_date = start_date
        if blogs is not None:
            self.blogs = blogs


class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blogger_id = db.Column(db.Integer, db.ForeignKey('blogger.id'),
                           nullable=False)
    blogger = db.relationship('Blogger', backref=db.backref('blogs'))

    title = db.Column(db.String(VCHAR_DEFAULT), nullable=False)
    page_url = db.Column(db.String(VCHAR_DEFAULT), nullable=False)
    feed_url = db.Column(db.String(VCHAR_DEFAULT), nullable=False)

    def __init__(self, title, page_url, feed_url, blogger=None):
        self.title = title
        self.page_url = page_url
        self.feed_url = feed_url
        if blogger is not None:
            self.blogger = blogger

    def sync_posts(self):
        last_post = db.session.query(Post)\
            .filter_by(blog=self)\
            .order_by(Post.date.desc()).first()
        feed = feedparser.parse(self.feed_url)
        feed_posts = map(Post.from_feed_entry, feed.entries)

        # The loop below assumes our feed entries are sorted by date, newest
        # first. This ensures just that:
        feed_posts = sorted([(post.date, post) for post in feed_posts])
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
                    # If a post has the same date as one already in the db (on
                    # the same blog), we use the title as an identifier.
                if post.date == last_post.date and post.title == last_post.title:
                    break

            post.blog = self
            db.session.add(post)
        db.session.commit()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(VCHAR_DEFAULT), nullable=False)
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
            if key in feed_entry:
                return date.fromtimestamp(time.mktime(feed_entry[key]))
        raise MalformedPostError("No publication date in post: %r" %
                                 feed_entry)

    @staticmethod
    def from_feed_entry(entry):
        """Read and construct Post object from ``entry``.

        ``entry`` should be a post object as returned by ``feedparser.parse``.

        If the post is invalid, raise a ``MalformedPostError`.

        This leaves the `blog` field emtpy; this must be filled in before the
        post is added to the database.
        """
        if 'title' not in entry:
            raise MalformedPostError("Post has no title: %r" % entry)
        if 'link' not in entry:
            raise MalformedPostError("Post has no url: %r" % entry)
        title = entry['title']
        post = Post()
        post.date = Post._get_pub_date(entry)
        post.title = title
        post.page_url = entry['link']

        return post


@app.route('/bloggers')
def show_bloggers():
    return render_template('bloggers.html',
                           bloggers=db.session.query(Blogger).all())

@app.route('/planet')
def show_planet():
    posts = db.session.query(Post).order_by(Post.date.desc())
    return render_template('planet.html', posts=posts)


if __name__ == '__main__':
    app.run(debug=True)
