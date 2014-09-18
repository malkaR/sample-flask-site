import sqlite3
import us
from flask import Flask, g, request
from flask.ext.restful import reqparse, abort, Api, Resource
from flask.ext.sqlalchemy import SQLAlchemy
from contextlib import closing

app = Flask(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
api = Api(app)
db = SQLAlchemy(app)
US_STATES = [state.abbr for state in us.states.STATES]


# Database Model
class Order(db.Model):
    __tablename__ =  'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    name = db.Column(db.String(120))
    # birthday = db.Column(db.DateTime, nullable=True)
    state = db.Column(db.String(2), nullable=True)
    # valid
    # failures

    def __init__(self, *args, **kwargs):
        for field in kwargs:
            setattr(self, field, kwargs[field])

    def __repr__(self):
        return '<Order %d>' % self.id

# Order validation 
parser = reqparse.RequestParser()
parser.add_argument('id', type=int, required=True)
parser.add_argument('name', type=str, required=True)
parser.add_argument('state', type=str, required=False, choices=US_STATES)

class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

    def put(self):
        args = parser.parse_args()
        print args
        order = Order(**args)
        print order.id
        print order.name
        db.session.add(order)
        db.session.commit()
        return {'success':True}

# Routes
api.add_resource(HelloWorld, '/')


if __name__ == '__main__':
    app.run()
