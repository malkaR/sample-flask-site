import os
import sqlite3
import sys
from contextlib import closing
sys.path.append(os.path.abspath(os.pardir))
import flaskr
from lettuce import *
from flask.ext.sqlalchemy import SQLAlchemy

@before.all
def set_up():
    """
    Create a new empty database.
    """
    os.environ['FLASKR_SETTINGS'] = 'settings_test.py'
    init_db()
    world.db = flaskr.db
    world.app = flaskr.app.test_client()

@after.all
def tear_down(total):
    """
    Delete the database file to isolate state between scenarios.
    """
    try:
        os.unlink(flaskr.app.config['DATABASE'])
    except OSError:
        pass

# Test Set Up Helper functions

def connect_db():
    return sqlite3.connect(flaskr.app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with flaskr.app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()