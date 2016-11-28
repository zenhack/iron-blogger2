#!/usr/bin/env python
#
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

from setuptools import setup, find_packages

import os
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Grab description for Pypi
with open(os.path.join(THIS_DIR, 'README.md')) as fhl:
    description = fhl.read()

setup(name='ironblogger',
      version='1.0',
      url='https://github.com/zenhack/iron-blogger2',
      packages=find_packages(),
      description="Iron Blogger Web Service, compete blog to blog, week to week"
      long_description=description,
      scripts=['scripts/ironblogger'],
      license='GPLv3',
      install_requires=[
          'Flask',
          'Flask-Admin',
          'Flask-Login>=0.3.2',
          'Flask-Mail',
          'Flask-SQLAlchemy',
          'feedparser==5.1.3',
          'passlib',
          'PyYAML',
          'schema',
          'alembic',
          'arrow',
          'six',
          # Depending on your database, you may need one of the following.
          # uncomment as needed:
          #
          # for postgresql:
          # 'psycopg2',
      ])
