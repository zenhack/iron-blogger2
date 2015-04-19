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

from ironblogger.app import app
from ironblogger.model import Blogger, Blog, MalformedPostError, db


def create_rounds(until=None):
    """Create missing BloggerRounds for all Bloggers.

    This works like the Blogger class's method of the same name, except that
    it creates rounds for all bloggers.
    """
    # If we left this out, the method would do the same thing, but
    # if this runs across a round boundary we may get different numbers of
    # rounds for different bloggers:
    if until is None:
        until = datetime.now()

    with app.test_request_context():
        bloggers = db.session.query(Blogger).all()
        for blogger in bloggers:
            blogger.create_rounds(until)


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
    with app.test_request_context():
        db.create_all()
        session = db.session

        yml = yaml.load(file)
        for blogger in yml.iteritems():
            name = blogger[0]
            start_date = blogger[1]['start']
            model = Blogger(name, start_date)
            for link in blogger[1]['links']:
                model.blogs.append(Blog(*link))
            session.add(model)
        session.commit()


def assign_posts(until=None):
    """Assign posts to rounds."""


def sync_posts():
    """Download new posts"""
    logging.info('Syncing posts')
    with app.test_request_context():
        blogs = db.session.query(Blog).all()
        for blog in blogs:
            try:
                blog.sync_posts()
            except MalformedPostError as e:
                logging.info('%s', e)
