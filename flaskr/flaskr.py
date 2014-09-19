import sqlite3
import us
import csv
import os
import json
from flask import Flask, g, request, make_response
from flask.ext.restful import reqparse, abort, Api, Resource
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

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
    email = db.Column(db.String(120), nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    state = db.Column(db.String(2), nullable=True)
    zipcode = db.Column(db.Integer, nullable=True)

    # valid
    # failures

    def __init__(self, *args, **kwargs):
        for field in kwargs:
            setattr(self, field, kwargs[field])

    def __repr__(self):
        return '<Order %d>' % self.id

# Order validation 


class Orders(Resource):
    def get(self):
        return {'hello': 'world'}

    def put(self):
        lines = request.form['data'].split('\\n')
        csvreader = csv.reader(lines, delimiter='|')
        headers = csvreader.next()
        values = {}
        for row in csvreader:
            for i, item in enumerate(row):
                if headers[i] == 'birthday':
                    item = datetime.strptime(item, '%b %d, %Y').date()
                values.update({headers[i]: item}) 
            order = Order(**values)
            db.session.add(order)
        db.session.commit()
        return {'success':True}


# Routes
api.add_resource(Orders, '/')

    

if __name__ == '__main__':
    app.run()
