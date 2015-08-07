"""This module contains subroutines not used by the webapp itself.

Most of these are periodic jobs like downloading new posts, computing the
scores for the round, etc. It makes sense to run these as a cron job or
similar.

Routines defined here do not assume they're running in an application context.
Those which need one create one themselves.
"""

import yaml
import logging
from datetime import datetime
from os import path

import ironblogger
from .app import app
from .model import Blogger, Blog, Post, MalformedPostError, db

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
        start_date = blogger[1]['start']
        model = Blogger(name=name, start_date=start_date)
        for link in blogger[1]['links']:
            model.blogs.append(Blog(title=link[0],
                                    page_url=link[1],
                                    feed_url=link[2],
                                    ))
        session.add(model)
    session.commit()


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
