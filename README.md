Iron Blogger 2 is a reimplementation of the original [iron_blogger][1].
The consensus among those of the original's users who are also
developers is that it is unmaintainable, and a rewrite is needed.

Iron Blogger 2 is just barely feature complete enough to start using; 
Much more work is needed. Patches welcome!

# Setting Up a Development Environment

Use of [virtualenv][1] is recommended for development. In this 
directory, execute:

    virtualenv .venv
    source .venv/bin/activate
    pip install -e .
    pip install -r test-requirements.txt

Any directory can be used for the virtual environment, but `.venv` is 
preferred, and there's a rule in `.gitignore` which will keep you from 
accidentally committing it to the repository. The first pip command 
installs ironblogger in "editable" mode, so that changes you make to the 
source tree will be picked up automatically. The second installs 
dependencies for running the test suite. The rest of this document

Copy `example.wsgi.py` to `wsgi.py` and edit the configuration therein.
The `ironblogger` command described below must be run from within the 
same directory as `wsgi.py`.

To initialize the database, make sure `wsgi.py` specifies the right url 
for the database, and run `ironblogger init-db`

Iron Blogger 2 is a [Flask][2] app. A stand-alone development server can
be started with:

    ironblogger serve

At which point, the application will be available at
<http://localhost:5000>.

###Static assets

Static assets are managed via Bower (http://bower.io) and can be installed with the command `bower install`. This helps keep our standard css/js/font libraries orderly. 

Bower itself can be installed with `npm install -g bower`


The `bloggers.yml` file used by the old iron blogger software can be 
imported via:

    ironblogger import < bloggers.yml

paultag's repository has a version of [bloggers.yml][4] that roughly 
reflects the roster of Boston-area participants the last time the 
original software was being used.

Once the database is populated with bloggers/blogs, posts can be downloaded
by running:

    ironblogger sync-posts

Then, `ironblogger assign-rounds` will update accounting information.

## Unit Tests

We use [pytest][7] for unit testing. Running the tests is simply a 
matter of executing:

    py.test

It's configured to display code coverage statistics as well.

New tests should be placed in a file matching `tests/test_*`; This 
allows pytest to pick them up automatically.

## Useful tips

* The command `ironblogger shell` will open a python interpreter prompt 
  that has already loaded the settings in wsgi.py, and is running inside 
  of a Flask request context, with an active database connection. This allows
  you to make calls to various parts of the code that don't otherwise work
  without a bit of setup.
* As of right now, while there's an admin panel available at `<main page 
  url>/admin`, no users will exist by default. You can add one manually 
  by dropping into the python shell using `ironblogger shell`, and running:

    from ironblogger.model import *
    u = User(name='my_user', is_admin=True)
    u.set_password('secret')
    db.session.add(u)
    db.session.commit()

# Setting Up In Production

## Web Server

Iron Blogger is a standard [wsgi][5] application; the `wsgi.py` that 
supplies the configuration also provides the `application` variable 
required by wsgi; it should work with any web server which supports the 
standard.

## Database

Iron Blogger 2 has only been tested with SQLite and PostgreSQL. The 
latter should be used for production deployments; SQLite does not allow 
concurrent processes to safely access the database, and Iron Blogger 
requires this to fetch new posts and do bookkeeping. SQLite is fine 
during development however, where the update tasks are typically run 
manually and so there is a low risk of data corruption. To use postgres, 
you'll need the additional python package `psycopg2`; read the comments 
in `setup.py` to learn how to set that up.

## Syncing Posts & Bookkeeping

The recommended approach to keeping Iron Blogger's database up to date 
is to add the `ironblogger sync-posts` and `ironblogger assign-rounds` 
commands described above to a cron job. These must be run from the 
directory containing `wsgi.py`.

## Openshift

Iron Blogger comes ready to run on [Openshift][6]. Have a look at 
`example-openshift.wsgi.py` for instructions. You'll need the postgres 
and cron cartridges installed. The scripts in the `.openshift` directory 
will take care of keeping the database up to date (new posts will be 
downloaded once per hour).

# License

Iron Blogger 2 is Free Software, released under the GPL3. A list of
its authors can be found in the file `AUTHORS`.

[1]: https://github.com/paultag/iron-blogger
[2]: http://flask.pocoo.org/
[3]: https://virtualenv.pypa.io/en/latest/
[4]: https://raw.githubusercontent.com/paultag/iron-blogger/master/bloggers.yml
[5]: https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface
[6]: https://www.openshift.com/
