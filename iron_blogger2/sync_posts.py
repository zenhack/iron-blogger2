
from iron_blogger2.app import *

if __name__ == '__main__':
    blogs = db.session.query(Blog).all()
    for blog in blogs:
        blog.sync_posts()
