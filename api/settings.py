# configuration
import os

DATABASE = '/tmp/flaskr.db'
TEST_DATABASE = '/tmp/test_flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/flaskr.db'
PROJECT_DIR = os.path.abspath(os.pardir)

