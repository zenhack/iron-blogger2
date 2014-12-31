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

from iron_blogger2.app import *
import sys
import yaml
import logging



def sync_posts():
    with app.test_request_context():
        blogs = db.session.query(Blog).all()
        for blog in blogs:
            try:
                blog.sync_posts()
            except MalformedPostError as e:
                logging.info('%s', e)


def import_bloggers(file):
    """Import the bloggers (and their blogs) read from ``file``.

    ``file`` should be a file like object, which contains a yaml document.
    The document should be of the same formed as the file ``bloggers.yml`` in
    the old iron-blogger implementation, i.e. the contents of the document
    should be a dictionary:

    * whose keys are the usernames/handles of the bloggers
    * whose values are each a dictionary with the keys:
       * ``start``, which should be date of the form ``YYYY-MM-DD``,
          representing the date on which the blogger joined Iron Blogger
       * ``links``, which should be a list of lists of the form
         ``[title, page_url, feed_url]`` where
         * ``title`` is the title of the blog (in many cases, just the name of
           the blogger).
         * ``page_url`` is the url for the human-readable web page of the blog.
         * ``feed_url`` is the url for the rss or atom feed for the blog.

    ``import_bloggers`` will create the database if it does not exist, and
    populat it with the contents of ``file``.
    """
    with app.test_request_context():
        db.create_all()
        session = db.session

        yml = yaml.load(file)
        for blogger in yml.iteritems():
            name = blogger[0]
            start_date = blogger[1]['start']
            model = Blogger(name, start_date)
            for link in blogger[1]['links']:
                model.blogs.append(Blog(*link))
            session.add(model)
        session.commit()


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
