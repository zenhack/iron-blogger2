"""This module contains subroutines not used by the webapp itself.

Most of these are periodic jobs like downloading new posts, computing the
scores for the round, etc. It makes sense to run these as a cron job or
similar.

Routines defined here do not assume they're running in an application context.
Those which need one create one themselves.
"""

import yaml
import json
import arrow
import logging
from getpass import getpass
from datetime import datetime
from os import path

import ironblogger
from .app import app
from .model import Blogger, Blog, Post, User, MalformedPostError, db

from alembic.config import Config
from alembic import command


def with_context(task):
    with app.test_request_context():
        task()


def init_db():
    db.create_all()
    alembic_cfg = Config(path.join(
        path.dirname(ironblogger.__file__),
        "..",
        "alembic.ini"
    ))
    command.stamp(alembic_cfg, 'head')


def assign_rounds(since=None, until=None):
    """Assign posts to rounds."""
    if until is None:
        until = datetime.utcnow()
    if since is None:
        since = db.session.query(Blogger.start_date)\
                          .order_by(Blogger.start_date).first()[0]

    posts = db.session.query(Post)\
        .filter(Post.counts_for == None,
                Post.timestamp >= since,
                Post.timestamp <= until)\
        .order_by(Post.timestamp.asc()).all()

    for post in posts:
        post.assign_round()

    db.session.commit()


def import_bloggers(file):
    """Import the bloggers (and their blogs) read from ``file``.

    ``file`` should be a file like object, which contains a yaml document.
    The document should be of the same formed as the file ``bloggers.yml`` in
    the old iron-blogger implementation, i.e. the contents of the document
    should be a dictionary:

    * whose keys are the usernames/handles of the bloggers
    * whose values are each a dictionary with the keys:
       * ``start``, which should be date of the form ``YYYY-MM-DD``,
          representing the date on which the blogger joined Iron Blogger
       * ``links``, which should be a list of lists of the form
         ``[title, page_url, feed_url]`` where
         * ``title`` is the title of the blog (in many cases, just the name of
           the blogger).
         * ``page_url`` is the url for the human-readable web page of the blog.
         * ``feed_url`` is the url for the rss or atom feed for the blog.

    ``import_bloggers`` will create the database if it does not exist, and
    populate it with the contents of ``file``.
    """
    session = db.session

    yml = yaml.load(file)
    for blogger in yml.iteritems():
        name = blogger[0]

        # We have to be careful when parsing the date (typically in
        # YYYY-MM-DD form). If we just hand it off unmodified, it will be
        # interpreted in UTC, but the file format requires local time.
        # Otherwise, if the file indicates that a start date is on the first
        # day of a round, and the local timezone is west of UTC, they will be
        # entered as having started the previous day, and thus the previous
        # week.
        start_date = arrow.get(blogger[1]['start']).naive
        start_date = arrow.get(start_date, app.config['IB2_TIMEZONE'])
        start_date = start_date.to('UTC').datetime

        model = Blogger(name=name, start_date=start_date)
        for link in blogger[1]['links']:
            model.blogs.append(Blog(title=link[0],
                                    page_url=link[1],
                                    feed_url=link[2],
                                    ))
        session.add(model)
    session.commit()


def export_bloggers(file):
    """Inverse of `import_bloggers`.

    This outputs a file as described in the docstring for `import_bloggers`,
    based on the contents of the database.
    """
    result = {}
    bloggers = db.session.query(Blogger).all()
    for blogger in bloggers:
        result[blogger.name] = {
            'start': blogger.start_date.strftime("%F"),
            'links': [
                [blog.title, blog.page_url, blog.feed_url]
                for blog in blogger.blogs
            ]
        }
    # If we use the yaml library to dump, We'll get !!python/unicode
    # everywhere, which... ew. Fortunately, JSON is a strict subset of yaml,
    # and it covers enough ground for our purposes, so we'll just output that:
    json.dump(result, file)


def shell():
    """Launch a python interpreter.

    The CLI does this inside of an app context, so it's a convienent way to
    play with the API.
    """
    import code
    code.interact(local=locals())


def sync_posts():
    """Download new posts"""
    logging.info('Syncing posts')
    blogs = db.session.query(Blog).all()
    for blog in blogs:
        try:
            blog.sync_posts()
        except MalformedPostError as e:
            logging.info('%s', e)


def make_admin():
    """Create an admin user.

    Prompts the user via the CLI for a username and password, and creates
    an admin user.
    """
    username = raw_input('Admin username: ')
    while True:
        pw1 = getpass()
        pw2 = getpass('Password (again):')
        if pw1 == pw2:
            break
        print('Passwords did not match, try again.')
    user = User(name=username, is_admin=True)
    user.set_password(pw1)
    db.session.add(user)
    db.session.commit()
