"""Utility module for dealing with dates.

Most of the Iron Blogger specific logic is book keeping about dates;
unsurprisingly there are a few generic helpers we need that aren't in the
standard library.
"""
from datetime import timedelta
import arrow
from .app import app

ROUND_LEN = timedelta(weeks=1)


def to_dbtime(dt):
    return set_tz(dt).replace(tzinfo=None)


def set_tz(dt):
    return arrow.get(dt).to('UTC').datetime


def in_localtime(dt):
    return arrow.get(set_tz(dt)).to(app.config['IB2_TIMEZONE']).datetime


def dst_adjust(due):
    """Adjust the duedate due to account for having crossed a DST boundary.

    When performing calculations with due dates, it can be convienient to move
    forward or back by adding/subtracting the length of a round. Unfortunately
    crossing a DST boundary messes with this. if `due` is a duedate, possibly
    skewed by 1 hour due to such computations, `dst_adjust(due)` is the
    corrected due date.

    This function should be used in most cases where arithemtic is being
    performed with duedates.
    """
    if duedate(due) < due:
        due = duedate(due)
    elif duedate(due) > due:
        due = duedate(due - ROUND_LEN)
    return due


def duedate(post_date):
    """The due date for which a post published on ``post_date`` counts.

    preconditions:

        isinstance(post_date, datetime)
    """

    post_date = arrow.get(post_date).to(app.config['IB2_TIMEZONE'])
    # Luckily, the arrow library considers Sunday to be the last day of the
    # week, so we don't need to do any special adjustment. NOTE: we need to
    # return an actual datetime object; sqlalchemy won't store an Arrow in the
    # database.
    return post_date.ceil('week').to('UTC').datetime


def rssdate(date_obj):
    """Format ``date_obj`` as needed by rss.

    This is *almost* as specified in rfc822, but the year is 4 digits instead
    of two.
    """
    return arrow.get(date_obj).to(app.config['IB2_TIMEZONE']).strftime('%d %b %Y %T %z')


def round_diff(last, first):
    """Return the number of rounds between two duedates."""
    # The call to round() is necessary, since if the dates cross a dst
    # boundary, it won't be a whole number of weeks.
    return round((last - first).total_seconds()/ROUND_LEN.total_seconds())
