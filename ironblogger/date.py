"""Utility module for dealing with dates.

Most of the Iron Blogger specific logic is book keeping about dates;
unsurprisingly there are a few generic helpers we need that aren't in the
standard library.

The coding style in this module is very defensive; the inputs to each
function are checked and will raise assertions if they are incorrect.

A guide to the names for types used in this module:

    * An arrow is an instance of `arrow.arrow.Arrow` (the standard
      arrow type from the arrow library).
    * A local arrow is an arrow whose timezone matches Iron Blogger's
      configured timezone.
    * A duedate is a local arrow whose value is that of a deadline for iron
      blogger. If `due` is a duedate, the invariant `duedate(due) == due`
      must hold.
    * a dbtime is a naive datetime; these are stored in the database and
      are implicitly UTC.
"""
from datetime import timedelta, datetime
import arrow
from arrow.arrow import Arrow
from .app import app

ROUND_LEN = timedelta(weeks=1)

# Each of the _assert_* functions below assert that the argument is of the
# named type, according to the definitions in this module's docstring.


def _assert_dbtime(dt):
    assert isinstance(dt, datetime) and dt.tzinfo is None, \
        "Expected naive datetime but got %r" % dt


def _assert_local_arrow(arr):
    assert isinstance(arr, Arrow), "BUG: Expected arrow but got %r" % arr
    assert arr.to(app.config["IB2_TIMEZONE"]).tzinfo == arr.tzinfo, \
        "BUG: Arrow %r is not in the configured Iron Blogger timezone."


def _assert_duedate(arr):
    _assert_local_arrow(arr)
    assert duedate(arr) == arr, \
        "BUG: Expected duedate but got %r" % arr


def to_dbtime(arr):
    _assert_local_arrow(arr)
    return arr.to('UTC').datetime.replace(tzinfo=None)


def from_dbtime(dt):
    _assert_dbtime(dt)
    return arrow.get(dt).to('UTC').to(app.config['IB2_TIMEZONE'])


def from_feedtime(feedtime):
    """Extract a local arrow from feed entry.

    `feedtime` should be the value of a feed entry's publication date.
    It's not entirely clear to me what this is guaranteed to be, so the
    checking isn't as tight here as it is elsewhere in this module. We do
    verify that it's neither a naive datetime nor an arrow, which should be
    enough to ensure we're not mixing up the types.
    """
    assert not isinstance(feedtime, Arrow), \
        "BUG: passed Arrow to from_feedtime."
    assert not (isinstance(feedtime, datetime) and feedtime.tzinfo is None), \
        "BUG: passed naive datetime to from_feedtime."
    return arrow.get(feedtime).to(app.config['IB2_TIMEZONE'])


def duedate_seek(due, count):
    """Return the duedate `count` rounds after `due`.

    Earlier rounds may be found by supplying negative values for `count`.

    `due` must be a duedate.
    `count` must be an integer.
    """
    _assert_local_arrow(due)
    assert duedate(due) == due, \
        "BUG: argument to duedate_seek must be a due date."
    return due.replace(weeks=count)


def duedate(post_date):
    """The due date for which a post published on ``post_date`` counts.

    `post_date` must be a local arrow.
    """
    _assert_local_arrow(post_date)

    # Luckily, the arrow library considers Sunday to be the last day of the
    # week, so we don't need to do any special adjustment.
    return post_date.ceil('week')


def rssdate(arr):
    """Format ``arr`` as needed by rss.

    This is *almost* as specified in rfc822, but the year is 4 digits instead
    of two.

    `arr` must be a local arrow
    """
    _assert_local_arrow(arr)
    return arr.strftime('%d %b %Y %T %z')


def round_diff(last, first):
    """Return the number of rounds between two duedates.

    both `first` and `last` must be duedates.
    """
    _assert_duedate(last)
    _assert_duedate(first)
    # The call to round() is necessary, since if the dates cross a dst
    # boundary, it won't be a whole number of weeks.
    return round((last - first).total_seconds()/ROUND_LEN.total_seconds())


def now():
    """Return the current time and date as a local arrow."""
    return arrow.now().to(app.config["IB2_TIMEZONE"])
