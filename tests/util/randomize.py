"""This package provides helpers for randomzied testsing."""
from random import Random
from ironblogger.app import db
from ironblogger.model import Blogger
from ironblogger.date import to_dbtime


def random_database(seed, now):
    """Generate a random database based on random seed `seed`.

    This expects to be run within an application context; after the call the
    objects will be stored in the associated datbase.

    Note that this function does not commit the changes to the database; the
    caller must do that themselves.
    """
    rand = Random(seed)

    blogger_choices = ['Alice', 'Bob', 'Cindy', 'Dave', 'Eve', 'Fred', 'Gina',
                       'Henry', 'Isabelle', 'Joe', 'Kate', 'Larry', 'Mallory',
                       'Nina', 'Owen', 'Patty', 'Quentin', 'Ron', 'Sarah',
                       'Tim', 'Uwe', 'Vincent', 'Wendy', 'Xavier', 'Yolanda',
                       'Zack']

    num_bloggers = rand.randint(0, len(blogger_choices) - 1)
    blogger_names = rand.sample(blogger_choices, num_bloggers)

    first_start_date = now.replace(weeks=-8)
    last_start_date = now.replace(weeks=+8)
    for name in blogger_names:
        start_date = random_arrow(rand, first_start_date, last_start_date)
        db.session.add(Blogger(name=name,
                               start_date=to_dbtime(start_date)))


def random_arrow(rand, start, end):
    """Generate a random arrow object in the range [start,end].

    `rand` is an instance of `Random`.
    """
    offset = rand.randint(0, (end - start).total_seconds())
    return start.replace(seconds=offset)
