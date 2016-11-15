"""This package provides helpers for randomzied testsing."""
from six.moves.urllib_parse import quote
import os
from ironblogger.app import db
from ironblogger.model import Blogger, Blog, Post, Party
from ironblogger.date import to_dbtime, duedate, duedate_seek
import arrow

random_ncalls = int(os.getenv('NUM_RANDOM_CALLS', '10'))


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

word_choices = [
    'the', 'of', 'to', 'and', 'a', 'in', 'is', 'it', 'you', 'that', 'he',
    'was', 'for', 'on', 'are', 'with', 'as', 'I', 'his', 'they', 'be', 'at',
    'one', 'have', 'this', 'from', 'or', 'had', 'by', 'hot', 'but', 'some',
    'what', 'there', 'we', 'can', 'out', 'other', 'were', 'all', 'your',
    'when', 'up', 'use', 'word', 'how', 'said', 'an', 'each', 'she', 'which',
    'do', 'their', 'time', 'if', 'will', 'way', 'about', 'many', 'then',
    'them', 'would', 'write', 'like', 'so', 'these', 'her', 'long', 'make',
    'thing', 'see', 'him', 'two', 'has', 'look', 'more', 'day', 'could',
    'go', 'come', 'did', 'my', 'sound', 'no', 'most', 'number', 'who',
    'over', 'know', 'water', 'than', 'call', 'first', 'people', 'may', 'down',
    'side', 'been', 'now', 'find', 'any', 'new', 'work', 'part', 'take',
    'get', 'place', 'made', 'live', 'where', 'after', 'back', 'little', 'only',
    'round', 'man', 'year', 'came', 'show', 'every', 'good', 'me', 'give',
    'our', 'under', '', 'Word', 'name', 'very', 'through', 'just', 'form',
    'much', 'great', 'think', 'say', 'help', 'low', 'line', 'before', 'turn',
    'cause', 'same', 'mean', 'differ', 'move', 'right', 'boy', 'old', 'too',
    'does', 'tell', 'sentence', 'set', 'three', 'want', 'air', 'well', 'also',
    'play', 'small', 'end', 'put', 'home', 'read', 'hand', 'port', 'large',
    'spell', 'add', 'even', 'land', 'here', 'must', 'big', 'high', 'such',
    'follow', 'act', 'why', 'ask', 'men', 'change', 'went', 'light', 'kind',
    'off', 'need', 'house', 'picture', 'try', 'us', 'again', 'animal', 'point',
    'mother', 'world', 'near', 'build', 'self', 'earth', 'father', 'head',
    'stand', 'own', 'page', 'should', 'country', 'found', 'answer', 'school',
    'grow', 'study', 'still', 'learn', 'plant', 'cover', 'food', 'sun',
    'four', 'thought', 'let', 'keep', 'eye', 'never', 'last', 'door',
    'between', 'city', 'tree', 'cross', 'since', 'hard', 'start', 'might',
    'story', 'saw', 'far', 'sea', 'draw', 'left', 'late', 'run', "don't",
    'while', 'press', 'close', 'night', 'real', 'life', 'few', 'stop',
]


def random_database(rand, now):
    """Generate a random database based on random number generator rand

    This expects to be run within an application context; after the call the
    objects will be stored in the associated datbase.

    Note that this function does not commit the changes to the database; the
    caller must do that themselves.
    """
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
    random_parties(rand, now, first_start_date)


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


def random_posts(rand, now, blog):
    # The exact numbers used here are somewhat arbitrary, but the general
    # principle is that they should slightly exceed realistic values.
    num_posts = rand.randint(0, 42)
    for i in range(num_posts):
        pub_date = random_arrow(rand,
                                now.replace(weeks=-20),
                                now.replace(weeks=+3))
        title = ' '.join([rand.choose(word_choices)
                          for n in range(rand.randint(0, 15))])
        summary = ' '.join([rand.choose(word_choices)
                            for n in range(rand.randint(25, 150))])
        db.session.add(Post(blog=blog,
                            timestamp=to_dbtime(pub_date),
                            guid='%x' % rand.getrandombits(128),
                            page_url=blog.page_url + '/%s' % quote(title),
                            title=title,
                            summary=summary))


def random_parties(rand, now, first_start_date):
    # The big constraint here is that this has to match what Iron blogger
    # normally does; parties' first/last duedates must be adjacent and
    # non-overlapping.
    #
    # TODO: this is hard to read; clean it up.
    end_parties = now.replace(weeks=+1)
    party_date = random_arrow(rand, first_start_date, end_parties)
    first_duedate = None
    while True:
        if first_duedate is not None:
            first_duedate = to_dbtime(first_duedate)
        last_duedate = duedate_seek(duedate(party_date), 1)
        party = Party(date=to_dbtime(party_date),
                      last_duedate=to_dbtime(last_duedate),
                      first_duedate=first_duedate,
                      spent=rand.randint(2000, 10000))
        first_duedate = duedate_seek(last_duedate, 1)
        db.session.add(party)
        if last_duedate >= end_parties:
            return
        party_date = random_arrow(rand,
                                  arrow.get(last_duedate),
                                  end_parties)


def random_arrow(rand, start, end):
    """Generate a random arrow object in the range [start,end].

    `rand` is an instance of `Random`.
    """
    offset = rand.randint(0, int((end - start).total_seconds()))
    return start.replace(seconds=offset)
