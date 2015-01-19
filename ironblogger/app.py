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
from flask import Flask, render_template
from ironblogger.model import db, Blogger, Post

app = Flask(__name__)


@app.route('/')
def show_index():
    return render_template('index.html')


@app.route('/bloggers')
def show_bloggers():
    return render_template('bloggers.html',
                           bloggers=db.session.query(Blogger).all())


@app.route('/all-posts')
def show_all_posts():
    posts = db.session.query(Post).order_by(Post.date.desc())
    return render_template('all-posts.html', posts=posts)
