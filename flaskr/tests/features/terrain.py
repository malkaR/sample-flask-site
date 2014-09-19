import os
import sqlite3
import sys
from contextlib import closing
sys.path.append(os.path.abspath(os.pardir))
import flaskr
from lettuce import *

@before.all
def setUp():
    os.environ['FLASKR_SETTINGS'] = 'settings_test.py'
    init_db() 
    world.db = flaskr.db
    world.app = flaskr.app.test_client() 

# @after.all
# def tearDown(self):
#   return
#     # os.unlink(flaskr.app.config['TEST_DATABASE'])

# Test Set Up Helper functions

def connect_db():
    return sqlite3.connect(flaskr.app.config['DATABASE'])

def init_db():
    try:
        # ensure no old database is present
        os.unlink(flaskr.app.config['DATABASE'])
    except OSError:
        print 'nothing to delete'
        print flaskr.app.config['DATABASE']
        
    with closing(connect_db()) as db:
        with flaskr.app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()