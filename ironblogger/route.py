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
from ironblogger.model import db, Blogger, Post
from ironblogger.app import app
from ironblogger import config


def render_template(*args, **kwargs):
    kwargs['cfg'] = config.cfg
    return flask.render_template(*args, **kwargs)


@app.route('/')
def show_index():
    return render_template('index.html')


@app.route('/status')
def show_status():
    blogger_debts = [(blogger, '$%d' % (5 * blogger.missed_posts()))
                     for blogger in db.session.query(Blogger).all()]
    return render_template('status.html', blogger_debts=blogger_debts)


@app.route('/bloggers')
def show_bloggers():
    return render_template('bloggers.html',
                           bloggers=db.session.query(Blogger).all())


@app.route('/all-posts')
def show_all_posts():
    posts = db.session.query(Post).order_by(Post.date.desc())
    return render_template('all-posts.html', posts=posts)
