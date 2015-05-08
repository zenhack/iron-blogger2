"""Utility module for dealing with dates.

Most of the Iron Blogger specific logic is book keeping about dates;
unsurprisingly there are a few generic helpers we need that aren't in the
standard library.
"""
from datetime import date, datetime, timedelta
from ironblogger import config

# This constant *has* to be defined somewhere, but I can't find it.
SUNDAY = timedelta(days=date(2015, 3, 29).weekday())
ROUND_LEN = timedelta(weeks=1)


def duedate(post_date):
    """The due date for which a post published on ``post_date`` counts.

    preconditions:

        isinstance(post_date, datetime)
    """
    weekday = post_date.weekday()
    # The due date should be upcoming *end* of a Sunday, hence the +1. Without
    # this, a timestamp on a Sunday would always come *after* its duedate.
    due_date = post_date - timedelta(days=weekday) + SUNDAY + timedelta(days=1)
    return datetime(due_date.year, due_date.month, due_date.day)


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
