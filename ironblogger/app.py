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
from flask.ext.login import LoginManager
from ironblogger.model import db, User
app = flask.Flask(__name__)

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).filter_by(name=user_id).first()
