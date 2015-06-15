# Copyright 2014 Ian Denhardt <ian@zenhack.net>
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

import argparse
from ironblogger.tasks import *
from ironblogger.app import app

commands = {
    'init-db': (
        init_db,
        "Initialize the database."
    ),
    'import': (
        lambda: import_bloggers(sys.stdin),
        "Import bloggers from yaml file."
    ),
    'serve': (
        lambda: app.run(debug=True),
        "Start the app server (in debug mode)."
    ),
    'shell': (
        shell,
        "Start a python shell inside the app context."
    ),
    'sync-posts': (
        sync_posts,
        "Syncronize posts with blogs."
    ),
    'assign-rounds': (
        assign_rounds,
        "Assign posts to rounds."
    ),
}

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='command')

for command_name in commands.keys():
    subparsers.add_parser(command_name, help=commands[command_name][1])

def main():
    args = parser.parse_args()
    with_context(commands[args.command][0])
