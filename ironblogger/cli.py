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

import sys

from ironblogger.tasks import import_bloggers, sync_posts
from ironblogger.app import app


def usage(exit_status=1):
    usage = '\n'.join([
        "Usage:",
        "",
        "    ironblogger import         # import bloggers from yaml file.",
        "    ironblogger serve          # start the app server (in debug mode).",
        "    ironblogger sync-posts     # syncronize posts with blogs.",
        "    ironblogger help           # show this help message.",
        "    ironblogger help <command> # show detailed help for <command>.",
    ])
    print(usage)
    sys.exit(exit_status)


def show_help(*args):
    if len(args) == 0:
        usage(0)
    else:
        print("command help not yet implemented")


def main():
    if len(sys.argv) < 2:
        usage()
    commands = {
        'help': lambda: show_help(*sys.argv[2:]),
        'import': lambda: import_bloggers(sys.stdin),
        'serve': lambda: app.run(debug=True),
        'sync-posts': sync_posts,
    }
    commands[sys.argv[1]]()
