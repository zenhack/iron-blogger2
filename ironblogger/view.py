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
import flask
from flask import make_response, request, url_for
from flask.ext.login import login_user, logout_user, login_required, LoginManager

from .app import app
from .model import db, Blogger, Blog, Post, Payment, Party, User
from .model import DEBT_PER_POST, LATE_PENALTY, MAX_DEBT
from .date import duedate, ROUND_LEN, round_diff, set_tz, in_localtime, \
    to_dbtime, dst_adjust
from collections import defaultdict
from datetime import datetime
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


@app.route('/status')
def show_status():
    # We're going to build up a somewhat complex data structure describing the
    # posting activity for the range of weeks corresponding to the page we've
    # been asked to display. We construct it in stages, but the final data
    # structure is formatted as follows:
    #
    # - A list of pairs `(due, info)`, sorted by `due`, where:
    #   - `due` is datetime object in the local timezone, representing a
    #     duedate.
    #   - `info` is a list of dictionaries with two elements:
    #     - 'missing-in-action', which is an (alphabetical) list of the
    #       bloggers who did not post for the week with duedate `due`.
    #     - 'posts', a list of dictionaries containing various information
    #       about each post that was either posted during that week or counted
    #       for that week. Note that late posts will appear in two places.
    #
    # Rough example:
    #
    # [ (duedate1, {
    #       'missing-in-action: ['alice', 'bob'],
    #       'posts': [{...}, {...}, {...}, ...],
    #    }),
    #   (duedate2, {
    #       'missing-in-action': ['bob'],
    #       'posts': [{...}, {...}, {...}, ...],
    #    }),
    #   ...
    # ]


    DEFAULT_PAGE_SIZE=5

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
    first_round = duedate(first_round[0])


    # Find the the current round:
    current_round = duedate(datetime.utcnow())


    # Work out how many pages there are, and what the bounds of the current page
    # are:
    num_rounds = round_diff(current_round, first_round)
    pageinfo = _page_args(item_count=num_rounds, size=DEFAULT_PAGE_SIZE)
    start_round = current_round - (ROUND_LEN * pageinfo['size'] * pageinfo['num'])
    stop_round  = start_round - (ROUND_LEN * pageinfo['size'])

    # Get a set of the names of all the bloggers. Same trick with the
    # row/tuple.
    all_bloggers = db.session.query(Blogger.name).all()
    all_bloggers = set([row[0] for row in all_bloggers])

    # Collect all of the posts we need to display. This includes (1) any post
    # that counts for some round on the current page, and (2) any post which
    # was published during one of those rounds AND does not count for *any*
    # round (extra posts):
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

    # Massage the information about the posts into the format we're going to
    # pass to the template. We accumulate the posts into one big list. we'll
    # sort them into rounds shortly.
    all_post_views = []
    for post in posts:
        post_view = {
            'title'     : post.title,
            'page_url'  : post.page_url,
            'author'    : post.blog.blogger.name,
            'blog_title': post.blog.title,
            'blog_url'  : post.blog.page_url,
            'timestamp' : in_localtime(post.timestamp),
            'counts_for': in_localtime(post.counts_for),
            'late?'     : post.counts_for is not None and
                duedate(post.timestamp) != duedate(post.counts_for),
            'bonus?'    : post.counts_for is None,
        }
        all_post_views.append(post_view)

    # We're going to build up a dictionary mapping dates to lists of posts.
    rounds = defaultdict(list)
    for view in all_post_views:
        rounds[in_localtime(duedate(view['timestamp']))].append(view)
        if view['counts_for'] is not None and view['late?']:
            rounds[view['counts_for']].append(view)

    # Now add in information about what bloggers didn't post.
    for k in rounds.keys():
        active = set([post['author'] for post in rounds[k]])
        missing = all_bloggers.copy() - active
        rounds[k] = {
            'posts': rounds[k],
            'missing-in-action': sorted(missing),
        }

    # Just before we pass the data into the template, we convert it to a
    # (sorted) list of paris, so the weeks come out in order.
    return render_template('status.html',
                           rounds=sorted(rounds.iteritems(), reverse=True),
                           pageinfo=pageinfo)


def build_ledger(start, stop):
    if start is None:
        start = db.session.query(Blogger.start_date)\
            .order_by(Blogger.start_date.asc()).first()
        if start is None:
            # It doesn't really matter what we put here, since there are no
            # bloggers, and thus it won't affect the output, but it has to be
            # *something* to avoid raising exceptions where it is used.
            start = datetime.utcnow()
        else:
            start = start[0]

    if stop is None:
        stop = datetime.utcnow()

    start = duedate(start)
    stop = duedate(stop)
    data = {'bloggers': []}
    bloggers = db.session.query(Blogger)\
        .filter(Blogger.start_date < to_dbtime(stop))\
        .order_by(Blogger.name).all()
    total_paid = 0
    total_incurred = 0
    for blogger in bloggers:
        first_duedate = duedate(blogger.start_date)
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
        ledger = build_ledger(dst_adjust(set_tz(parties[0].last_duedate) + ROUND_LEN), None)
        ledger['date'] = None
        ledger['total']['spent'] = 0
        info.append(ledger)
    for party in parties:
        ledger = build_ledger(party.first_duedate, party.last_duedate)
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
