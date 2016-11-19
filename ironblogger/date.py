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

from typing import NewType

DBTime = NewType('DBTime', datetime)
FeedTime = NewType('FeedTime', str)

# should be Arrow, but we don't have stubs for that yet:
LocalArrow = NewType('LocalArrow', Arrow)
DueDate = NewType('DueDate', Arrow)


ROUND_LEN = timedelta(weeks=1)

# Each of the _assert_* functions below assert that the argument is of the
# named type, according to the definitions in this module's docstring.


def to_dbtime(arr: LocalArrow) -> DBTime:
    return DBTime(arr.to('UTC').datetime.replace(tzinfo=None))


def from_dbtime(dt: DBTime) -> LocalArrow:
    return LocalArrow(arrow.get(dt).to('UTC').to(app.config['IB2_TIMEZONE']))


def from_feedtime(feedtime: FeedTime) -> LocalArrow:
    """Extract a local arrow from feed entry.

    `feedtime` should be the value of a feed entry's publication date.
    It's not entirely clear to me what this is guaranteed to be, so the
    checking isn't as tight here as it is elsewhere in this module. We do
    verify that it's neither a naive datetime nor an arrow, which should be
    enough to ensure we're not mixing up the types.
    """
    return LocalArrow(arrow.get(feedtime).to(app.config['IB2_TIMEZONE']))


def duedate_seek(due: DueDate, count: int) -> DueDate:
    """Return the duedate `count` rounds after `due`.

    Earlier rounds may be found by supplying negative values for `count`.

    `due` must be a duedate.
    `count` must be an integer.
    """
    return DueDate(due.replace(weeks=count))


def duedate(post_date: LocalArrow) -> DueDate:
    """The due date for which a post published on ``post_date`` counts.

    `post_date` must be a local arrow.
    """

    # Luckily, the arrow library considers Sunday to be the last day of the
    # week, so we don't need to do any special adjustment.
    return DueDate(post_date.ceil('week'))


def rssdate(arr: LocalArrow) -> FeedTime:
    """Format ``arr`` as needed by rss.

    This is *almost* as specified in rfc822, but the year is 4 digits instead
    of two.

    `arr` must be a local arrow
    """
    return FeedTime(arr.strftime('%d %b %Y %T %z'))


def round_diff(last: DueDate, first: DueDate) -> int:
    """Return the number of rounds between two duedates.

    both `first` and `last` must be duedates.
    """
    # The call to round() is necessary, since if the dates cross a dst
    # boundary, it won't be a whole number of weeks.
    return round((last - first).total_seconds()/ROUND_LEN.total_seconds())


def now() -> LocalArrow:
    """Return the current time and date as a local arrow."""
    return LocalArrow(arrow.now().to(app.config["IB2_TIMEZONE"]))
