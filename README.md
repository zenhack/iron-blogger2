Iron Blogger 2 is a reimplementation of the original [iron_blogger][1].
The consensus among those of the original's users who are also
developers is that it is unmaintainable, and a rewrite is needed.

This is far from feature complete -- patches welcome.

As of right now Iron Blogger 2 can do the following:

* import the old bloggers.yml file format into an sql database.
* display a page equivalent to
  <http://boston.iron-blogger.com/pages/participants/> (though
  participants not in good standing are not currently supported).

Iron Blogger 2 is a [Flask][2] app. A stand-alone development server can
be started with:

    python -m iron_blogger2.app

Support for generating a static site may be added in the near future --
there is no requirement for dynamic content given the features of the
original software.

The old `bloggers.yml` file may be imported via:

    python -m iron_blogger2.import_bloggers < bloggers.yml

The database is currently created within the iron_blogger2 module
directory. This is considered a bug, and will be fixed soon.

Iron Blogger 2 is Free Software, released under the GPL3. A list of
its authors can be found in the file `AUTHORS`.

[1]: https://github.com/paultag/iron-blogger
[2]: http://flask.pocoo.org/
