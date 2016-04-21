# Copyright 2014-2016 Ian Denhardt <ian@zenhack.net>
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

from argparse import ArgumentParser
import sys

from .tasks import *
from .app import app

commands = {
    'init-db': dict(
        fn=init_db,
        help='initialize the database'),
    'import': dict(
        fn=lambda: import_bloggers(sys.stdin),
        help='import bloggers from yaml file.'),
    'export': dict(
        fn=lambda: export_bloggers(sys.stdout),
        help='export bloggers to yaml file.'),
    'make-admin': dict(
        fn=make_admin,
        help='interactively create an admin user.'),
    'serve': dict(
        fn=lambda: app.run(debug=True),
        help='start the app server (in debug mode).'),
    'send-reminders': dict(
        fn=send_reminders,
        help='send reminder emails.'),
    'shell': dict(
        fn=shell,
        help='start a python shell inside the app context.'),
    'fetch-posts': dict(
        fn=fetch_posts,
        help='fetch new posts from blogs'),
    'assign-rounds': dict(
        fn=assign_rounds,
        help='assign posts to rounds.'),
    'sync': dict(
        fn=sync,
        help='Download new posts and update accounting.'),
}

main_parser = ArgumentParser()

subcommands_parser = main_parser.add_subparsers()


def mk_wrapper_fn(cmd):
    def wrapper_fn(args):
        with app.test_request_context():
            commands[cmd]['fn']()
    return wrapper_fn


for cmd in commands.keys():
    subp = subcommands_parser.add_parser(
        cmd,
        help=commands[cmd]['help'])
    subp.set_defaults(func=mk_wrapper_fn(cmd))


def main():
    args = main_parser.parse_args()
    args.func(args)
