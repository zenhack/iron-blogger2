"""Utility module for dealing with dates.

Most of the Iron Blogger specific logic is book keeping about dates;
unsurprisingly there are a few generic helpers we need that aren't in the
standard library.
"""
from datetime import date
from ironblogger import config

# I'm in slight disbelief that these constants aren't defined somewhere
# obvious, but I can't find them in the libraries. (Ian)
ONE_DAY = date(2015, 1, 2) - date(2015, 1, 1)
ONE_WEEK = ONE_DAY * 7
SUNDAY = 6


def duedate(post_date):
    """The due date for which a post published on ``post_date`` counts.

    preconditions:

        isinstance(post_date, date)
    """
    weekday = post_date.weekday()
    return post_date + (ONE_DAY * (SUNDAY - weekday))


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
