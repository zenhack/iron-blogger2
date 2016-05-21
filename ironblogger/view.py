# Copyright 2014-2015 Ian Denhardt <ian@zenhack.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>
"""HTTP handlers.

"views" in django terminology, or "controllers" if you're coming from a rails
world or actually know what MVC is about.

The structure of this module is in a transitional period; We're working on
making things more readable and maintainable.

The old design was characterized by the use of procedural logic to build up an
ad-hoc data structure (e.g. dictionaries of dictionaries of lists of tuples...).
The code for this was generally hard to read, and it was hard to keep track of
the details of that data structure.

The new design defines classes for the data that will be passed to the
template, and tries as much as possible to keep the details of their structure
encapsulated. There are lots of convience methods decorated with @property for
use in the templates, which keeps the templates (relatively) logic free.

So far only the status page has been dealt with (and is not necessarily done).
The classes `RoundStatus` and `PostStatus` are the sort of class described
above.
"""
import flask
from flask import make_response, request, url_for
from flask.ext.login import login_user, logout_user, login_required, LoginManager

from .app import app
from .model import db, Blogger, Blog, Post, Payment, Party, User
from .model import DEBT_PER_POST, LATE_PENALTY, MAX_DEBT
from .date import duedate, round_diff, \
    from_dbtime, to_dbtime, duedate_seek, now
from sqlalchemy import and_, or_

# We don't reference this anywhere else in this file, but we're importing it
# for the side effect of defining the filters:
from . import template_filters


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User)\
        .filter_by(name=user_id).first()


def render_template(*args, **kwargs):
    kwargs['cfg'] = app.config
    return flask.render_template(*args, **kwargs)


class PostStatus(object):
    """Status view info for a post"""

    def __init__(self, post):
        self._post = post

    @property
    def author(self):
        return self._post.blog.blogger.name

    @property
    def blog_url(self):
        return self._post.blog.page_url

    @property
    def blog_title(self):
        return self._post.blog.title

    @property
    def counts_for(self):
        if self._post.counts_for is None:
            return None
        return from_dbtime(self._post.counts_for)

    @property
    def page_url(self):
        return self._post.page_url

    @property
    def pub_date(self):
        return from_dbtime(self._post.timestamp)

    @property
    def title(self):
        return self._post.title


class RoundStatus(object):
    """Status view info for a single round."""

    def __init__(self, due, bloggers):
        """Create a status info object.

        `due` is the duedate of the round for this object.
        `bloggers` is a list of all the participating bloggers.
        """
        self.due = due
        self.bloggers = bloggers
        self.posts = []

    def populate_posts(self, posts):
        """Collect all of the posts from `posts` that belong in this round.

        `posts` is a list of `Post` objects.

        `populate_posts` will add each post in `posts` that either:

            * Were published in the corresponding round, or
            * Were counted towards the corresponding round.
        """
        for post in posts:
            post_status = PostStatus(post)
            if duedate(from_dbtime(post.timestamp)) == self.due:
                self.posts.append(post_status)
            elif (post.counts_for is not None and
                  from_dbtime(post.counts_for) == self.due):
                self.posts.append(post_status)

    @property
    def missing_in_action(self):
        missing = set(self.bloggers)
        for post in self.posts:
            if post.counts_for == self.due:
                missing.remove(post.author)
        return sorted(list(missing))


@app.route('/status')
def show_status():
    DEFAULT_PAGE_SIZE = 5

    # Find the first round:
    first_round = db.session.query(Blogger.start_date)\
        .order_by(Blogger.start_date.asc()).first()
    if first_round is None:
        # There aren't any rounds at all, so we're done:
        return render_template('status.html',
                               rounds=[],
                               pageinfo=_page_args(item_count=0,
                                                   size=DEFAULT_PAGE_SIZE))
    # SQLAlchemy returns a tuple of the rows, so to actually get the date
    # object, we need to extract it:
    first_round = first_round[0]
    first_round = duedate(from_dbtime(first_round))


    # Find the the current round:
    current_round = duedate(now())


    # Work out how many pages there are, and what the bounds of the current page
    # are:
    num_rounds = round_diff(current_round, first_round)
    pageinfo = _page_args(item_count=num_rounds, size=DEFAULT_PAGE_SIZE)
    start_round = duedate_seek(current_round, -(pageinfo['size'] * pageinfo['num']))
    stop_round = duedate_seek(start_round, -pageinfo['size'])

    # Get a set of the names of all the bloggers. Same trick with the
    # row/tuple.
    all_bloggers = db.session.query(Blogger.name).all()
    all_bloggers = set([row[0] for row in all_bloggers])

    rounds = []
    for i in range(pageinfo['size']):
        rounds.append(RoundStatus(due=duedate_seek(start_round, -i),
                                  bloggers=all_bloggers))

    # Collect all of the posts we need to display. This includes (1) any post
    # that counts for some round on the current page, and (2) any post which
    # was published during one of those rounds AND does not count for *any*
    # round (extra posts):
    start_round = to_dbtime(rounds[0].due)
    stop_round = to_dbtime(rounds[-1].due)
    posts = db.session.query(Post).filter(or_(
        # First case: post isn't being counted, but was published in the right
        # time peroid:
        and_(Post.counts_for == None,
             Post.timestamp  <= start_round,
             Post.timestamp  >  stop_round),
        # Second case: Post counts for something in the right time period:
        and_(Post.counts_for <= start_round,
             Post.counts_for >  stop_round)
    )).order_by(Post.timestamp.desc()).all()

    for round in rounds:
        round.populate_posts(posts)

    return render_template('status.html',
                           rounds=rounds,
                           pageinfo=pageinfo)


def build_ledger(start, stop):
    """Build a ledger for the dates between start and stop, which must be duedates."""
    if start is None:
        start = db.session.query(Blogger.start_date)\
            .order_by(Blogger.start_date.asc()).first()
        if start is None:
            # It doesn't really matter what we put here, since there are no
            # bloggers, and thus it won't affect the output, but it has to be
            # *something* to avoid raising exceptions where it is used.
            start = duedate(now())
        else:
            start = duedate(from_dbtime(start[0]))

    if stop is None:
        stop = duedate(now())

    data = {'bloggers': []}
    bloggers = db.session.query(Blogger)\
        .filter(Blogger.start_date < to_dbtime(stop))\
        .order_by(Blogger.name).all()
    total_paid = 0
    total_incurred = 0
    for blogger in bloggers:
        first_duedate = duedate(from_dbtime(blogger.start_date))
        first_duedate = max(first_duedate, start)
        posts = db.session.query(Post)\
            .filter(Post.counts_for != None,
                    Post.counts_for >= to_dbtime(first_duedate),
                    Post.counts_for < to_dbtime(stop),
                    Post.blog_id == Blog.id,
                    Blog.blogger_id == blogger.id)\
            .order_by(Post.counts_for.desc()).all()
        num_rounds = round_diff(stop, first_duedate)
        missed = num_rounds - len(posts)
        incurred = DEBT_PER_POST * missed
        for post in posts:
            incurred += post.rounds_late() * LATE_PENALTY
        paid = 0
        payments = db.session.query(Payment.amount)\
            .filter(Payment.blogger_id == blogger.id,
                    Payment.duedate >= to_dbtime(first_duedate),
                    Payment.duedate < to_dbtime(stop)).all()
        for payment in payments:
            paid += payment.amount
        incurred = min(incurred, MAX_DEBT)
        data['bloggers'].append({
            'name': blogger.name,
            'incurred': incurred,
            'paid': paid,
            'owed': incurred - paid,
        })
        total_paid += paid
        total_incurred += incurred
    data['total'] = {
        'incurred': total_incurred,
        'paid': total_paid,
        'owed': total_incurred - total_paid,
    }
    return data


@app.route('/ledger')
def show_ledger():
    info = []
    parties = db.session.query(Party).order_by(Party.date.desc()).all()
    if len(parties) == 0:
        ledger = build_ledger(None, None)
        ledger['date'] = None
        ledger['total']['spent'] = 0
        info.append(ledger)
    elif parties[0].last_duedate is not None:
        # XXX: Party.last_duedate *should* always be a duedate already, but it
        # isn't, because the admin interface allows entering arbitrary dates,
        # and it's annoying for the admin to actually specify a proper duedate.
        # We should fix this in the UI, then add a migration script to fix
        # already-wonky databses. In the meantime, we explicitly get the
        # duedate:
        from_dbtime(parties[0].last_duedate)
        ledger = build_ledger(duedate_seek(from_dbtime(parties[0].last_duedate), +1), None)
        ledger['date'] = None
        ledger['total']['spent'] = 0
        info.append(ledger)
    for party in parties:
        # Same note about the call to duedate as above:
        ledger = build_ledger(from_dbtime(party.first_duedate) if party.first_duedate else None,
                              from_dbtime(party.last_duedate) if party.last_duedate else None)
        ledger['date'] = party.date
        ledger['total']['spent'] = party.spent
        info.append(ledger)
    return render_template('ledger.html', party_info=info)


@app.route('/bloggers')
def show_bloggers():
    return render_template('bloggers.html',
                           bloggers=db.session.query(Blogger).order_by(Blogger.name).all())


@app.route('/rss')
def show_rss():
    posts = db.session.query(Post).order_by(Post.timestamp.desc())
    resp = make_response(render_template('rss.xml', posts=posts), 200)
    resp.headers['Content-Type'] = 'application/rss+xml'
    return resp


def _page_args(item_count, num=0, size=None):
    """Extract pagination from the query string

    This should be called from a function which display paginated data.
    ``item_count`` should be the total number of items in the paginated
    data. ``num`` and ``size`` are the default page number and page size,
    respectively. These are used if the client does not specify a value.

    If size is ``None``, it defaults to ``app.config['IB2_POSTS_PER_PAGE']``.

    If the client provides invalid arguments or requests a page which does not
    exist, ``_parse_args`` will abort the request handler, and return a 400 or
    404 status to the client.

    The return value is a dictionary with the following contents:

        'num'  - The page number
        'size' - The number of items on a page
        'is_first' - True iff this is the first page of the data
        'is_last': - True iff this is the last page of the data
    """
    if size is None:
        size = app.config['IB2_POSTS_PER_PAGE']
    try:
        num = int(request.args.get('page', num))
        size = int(request.args.get('page_size', size))
    except ValueError:
        # arguments weren't integers
        flask.abort(400)
    if num < 0 or size < 1:
        # Illegal arguments; can't have a zero-sized page or
        # page before page 1
        flask.abort(404)
    if num * size > item_count and item_count > 0:
        # We don't have this many pages. We need to special case
        # post_count == 0, or this page would just always error
        # at us, but otherwise we want to complain.
        flask.abort(404)
    return {
        'num': num,
        'size': size,
        'is_first': num == 0,
        'is_last': (num + 1) * size > item_count,
    }


def _page_filter(query, page):
    """Restrict a SQLAlchemy query to the page specified by ``page``

    ``query`` should be the query to filter.
    ``page`` should be a dictionary as returned by ``_page_args``.

    Returns a new query with the additional constraints
    """
    return query.offset(page['num'] * page['size']).limit(page['size'])


@app.route('/posts')
def show_posts():
    post_count = db.session.query(Post).count()
    pageinfo = _page_args(item_count=post_count)
    posts = db.session.query(Post)\
        .order_by(Post.timestamp.desc())
    posts = _page_filter(posts, pageinfo).all()
    return render_template('posts.html',
                           pageinfo=pageinfo,
                           posts=posts)


@app.route('/')
def show_index():
    return flask.redirect(url_for('show_posts'))


@app.route('/about')
def show_about():
    return render_template('about.html')


@app.route('/login', methods=['POST'])
def do_login():
    user = load_user(request.form['username'])
    if user is not None and user.verify_password(request.form['password']):
        login_user(user)
        return flask.redirect(request.args.get('next') or url_for('show_index'))
    return render_template('login.html', msg='Bad username or password')


@app.route('/login', methods=['GET'])
def show_login():
    if app.config['IB2_FORCE_HTTPS_LOGIN'] and not request.is_secure:
        return flask.redirect(url_for('show_login',
                                      _external=True,
                                      _scheme='https'))
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def do_logout():
    logout_user()
    return flask.redirect(url_for('show_login'))
