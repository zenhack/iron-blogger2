"""This package provides helpers for randomzied testsing."""
from random import Random
from urllib import quote
from ironblogger.app import db
from ironblogger.model import Blogger, Blog
from ironblogger.date import to_dbtime


blogger_choices = ['Alice', 'Bob', 'Cindy', 'Dave', 'Eve', 'Fred', 'Gina',
                   'Henry', 'Isabelle', 'Joe', 'Kate', 'Larry', 'Mallory',
                   'Nina', 'Owen', 'Patty', 'Quentin', 'Ron', 'Sarah',
                   'Tim', 'Uwe', 'Vincent', 'Wendy', 'Xavier', 'Yolanda',
                   'Zack']

tld_choices = ['com', 'net', 'org']
proto_choices = ['http', 'https']

feed_url_format = '%(proto)://%(subdomain).example.%(tld)/%(title)/feed.xml'
blog_url_format = '%(proto)://%(subdomain).example.%(tld)/%(title)/'

blog_title_choices = [
    'Theoretical Piracy',
    'Fun With Crypto',
    'Neat Photos',
    'Yet Another Weblog',
    'Horrible Ideas',
]


def random_database(seed, now):
    """Generate a random database based on random seed `seed`.

    This expects to be run within an application context; after the call the
    objects will be stored in the associated datbase.

    Note that this function does not commit the changes to the database; the
    caller must do that themselves.
    """
    rand = Random(seed)

    num_bloggers = rand.randint(0, len(blogger_choices) - 1)
    blogger_names = rand.sample(blogger_choices, num_bloggers)

    first_start_date = now.replace(weeks=-8)
    last_start_date = now.replace(weeks=+8)
    for name in blogger_names:
        start_date = random_arrow(rand, first_start_date, last_start_date)
        blogger = Blogger(name=name,
                          start_date=to_dbtime(start_date))
        db.session.add(blogger)
        random_blogs(rand, now, blogger)


def random_blogs(rand, now, blogger):
    count = rand.randint(0, len(blog_title_choices) - 1)
    titles = rand.sample(blog_title_choices, count)
    for title in titles:
        page_url = '%(proto)s://%(subdomain)s.example.%(tld)s/%(title)s/' % {
            'title': quote(title),
            'tld': rand.choice(tld_choices),
            'proto': rand.choice(proto_choices),
            'subdomain': blogger.name.lower(),
        }
        feed_url = page_url + 'feed.xml'
        blog = Blog(blogger=blogger,
                    title=title,
                    page_url=page_url,
                    feed_url=feed_url)
        db.session.add(blog)



def random_arrow(rand, start, end):
    """Generate a random arrow object in the range [start,end].

    `rand` is an instance of `Random`.
    """
    offset = rand.randint(0, (end - start).total_seconds())
    return start.replace(seconds=offset)
