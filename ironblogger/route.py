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
from flask.ext.login import login_user, logout_user, login_required

from ironblogger.app import app, load_user
from ironblogger.model import db, Blogger, Blog, Post, Payment, Party
from ironblogger.model import DEBT_PER_POST, LATE_PENALTY
from ironblogger import config
from ironblogger.date import rssdate, duedate, ROUND_LEN, divide_timedelta
from ironblogger.currency import format_usd
from collections import defaultdict
from datetime import datetime


def render_template(*args, **kwargs):
    kwargs['cfg'] = config.cfg
    return flask.render_template(*args, **kwargs)


@app.route('/')
def show_index():
    return render_template('index.html')


@app.route('/status')
def show_status():
    posts = db.session.query(Post)\
        .filter(Post.blog_id == Blog.id,
                Blog.blogger_id == Blogger.id,
                Post.timestamp >= Blogger.start_date)\
        .order_by(Post.timestamp.desc()).all()
    rounds = defaultdict(list)
    for post in posts:
        post_view = {
            'title': post.title,
            'page_url'  : post.page_url,
            'author'    : post.blog.blogger.name,
            'blog_title': post.blog.title,
            'blog_url'  : post.blog.page_url,
            'timestamp' : post.timestamp,
            'counts_for': post.counts_for,
            'late?'     : duedate(post.timestamp) != post.counts_for,
        }
        rounds[duedate(post.timestamp)].append(post_view)
        if post_view['counts_for'] is not None and post_view['late?']:
            rounds[post.counts_for].append(post_view)
    return render_template('status.html',
                           rounds=sorted(rounds.iteritems(), reverse=True))


@app.route('/ledger')
def show_ledger():
    data = []
    now = datetime.now()
    bloggers = db.session.query(Blogger).all()
    total_paid = 0
    total_incurred = 0
    for blogger in bloggers:
        posts = db.session.query(Post)\
            .filter(Post.counts_for != None,
                    Post.counts_for >= blogger.start_date,
                    Post.counts_for < duedate(now),
                    Post.blog_id == Blog.id,
                    Blog.blogger_id == blogger.id)\
            .order_by(Post.counts_for.desc()).all()
        num_rounds = divide_timedelta(
            duedate(now - ROUND_LEN) - duedate(blogger.start_date),
            ROUND_LEN)
        missed = num_rounds - len(posts)
        print('%s missed %d posts.' % (blogger.name, missed))
        incurred = DEBT_PER_POST * missed
        for post in posts:
            incurred += post.rounds_late() * LATE_PENALTY
        paid = 0
        payments = db.session.query(Payment.amount)\
            .filter(Payment.blogger_id == blogger.id).all()
        for payment in payments:
            paid += payment.amount
        data.append({
            'name': blogger.name,
            'incurred': format_usd(incurred),
            'paid': format_usd(paid),
            'owed': format_usd(incurred - paid),
        })
        total_paid += paid
        total_incurred += incurred
    parties = db.session.query(Party).order_by(Party.date.desc()).all()
    spent = 0
    for party in parties:
        spent += party.spent
    parties = [{'date': party.date, 'spent': format_usd(party.spent)}
               for party in parties]
    return render_template(
        'ledger.html',
        bloggers=data,
        parties=parties,
        budget='%s (%s collected)' % (format_usd(total_incurred - spent),
                                      format_usd(total_paid)))


@app.route('/bloggers')
def show_bloggers():
    return render_template('bloggers.html',
                           bloggers=db.session.query(Blogger).all())


@app.route('/all-posts/rss')
def show_all_posts_rss():
    posts = db.session.query(Post).order_by(Post.timestamp.desc())
    resp = make_response(render_template('all-posts-rss.xml', posts=posts), 200)
    resp.headers['Content-Type'] = 'application/rss+xml'
    return resp


@app.route('/all-posts')
def show_all_posts():
    post_count = db.session.query(Post).count()
    try:
        page_num = int(request.args.get('page', '0'))
        page_size = int(request.args.get('page_size', '50'))
    except ValueError:
        # arguments weren't integers
        flask.abort(400)
    if page_num < 0 or page_size < 1:
        # Illegal arguments; can't have a zero-sized page or
        # page before page 1
        flask.abort(404)
    if page_num * page_size > post_count and post_count > 0:
        # We don't have this many pages. We need to special case
        # post_count == 0, or this page would just always error
        # at us, but otherwise we want to complain.
        flask.abort(404)
    posts = db.session.query(Post)\
        .order_by(Post.timestamp.desc())\
        .offset(page_num * page_size)\
        .limit(page_size).all()
    return render_template('all-posts.html',
                           page=page_num,
                           page_size=page_size,
                           total_post_count=post_count,
                           posts=posts,
                           rssdate=rssdate)


@app.route('/login', methods=['POST'])
def do_login():
    user = load_user(request.form['username'])
    if user is not None and user.verify_password(request.form['password']):
        login_user(user)
        return flask.redirect(request.args.get('next') or url_for('show_index'))
    return render_template('login.html', msg='Bad username or password')


@app.route('/login', methods=['GET'])
def show_login():
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
@login_required
def do_logout():
    logout_user()
    return flask.redirect(url_for('show_login'))
