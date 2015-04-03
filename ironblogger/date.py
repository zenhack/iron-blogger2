"""Utility module for dealing with dates.

Most of the Iron Blogger specific logic is book keeping about dates;
unsurprisingly there are a few generic helpers we need that aren't in the
standard library.
"""
from datetime import date, timedelta
from ironblogger import config

# This constant *has* to be defined somewhere, but I can't find it.
SUNDAY = date(2015, 3, 29).weekday()


def duedate(post_date):
    """The due date for which a post published on ``post_date`` counts.

    preconditions:

        isinstance(post_date, date)
    """
    weekday = post_date.weekday()
    return post_date + (timedelta(days=1) * (SUNDAY - weekday))


def rssdate(date_obj, cfg=None):
    """Format ``date_obj`` as needed by rss.

    This is *almost* as specified in rfc822, but the year is 4 digits instead
    of two.
    """
    if cfg is None:
        cfg = config.cfg
    timestamp = date_obj.strftime('%d %b %Y %T ')
    timezone = date_obj.strftime('%z')
    if timezone == '':
        timezone = cfg['timezone']
    return timestamp + timezone
