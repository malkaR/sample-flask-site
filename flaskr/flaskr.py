import sqlite3
import us
import csv
import os
import json
from flask import Flask, g, request, make_response
from flask.ext.restful import reqparse, abort, Api, Resource
from flask.ext.sqlalchemy import SQLAlchemy
from voluptuous import Schema, Required, All, Length, Range, Invalid, MultipleInvalid
from datetime import datetime, date

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

    valid = db.Column(db.Boolean, default=True)
    failures = db.Column(db.Text, nullable=True)

    def __init__(self, *args, **kwargs):
        for field in kwargs:
            setattr(self, field, kwargs[field])

    def __repr__(self):
        return '<Order %d>' % self.id

# Order validation 
def coerce(typ=int, column_name=None):
    
    def f(v):
        try:
            return typ(v)
        except ValueError as e:
            msg = 'Value: {}; Error: can not be converted to the {} type'.format(str(v), typ)
            if column_name:
                msg = 'Field: {}; '.format(column_name) + msg
            raise Invalid(msg)
    return f

def allowed_states():
    """
    No wine can ship to New Jersey, Connecticut, Pennsylvania, Massachusetts,
    Illinois, Idaho or Oregon
    """
    def f(v):
        if v in ['NJ', 'CT', 'PA', 'MA', 'OR', 'ID', 'IL']:
            msg = 'Field: state; Value: {}; Error: Wine can not ship to this state'.format(v)
            raise Invalid(msg)
        return v

    return f

schema = Schema({
    Required('id'): All(coerce(int, column_name='order_id'),),
    Required('name'): All(str, Length(min=1)),
    'email': str,
    'birthday' : date,
    'state': All(str, allowed_states()),
    'zipcode': str
})

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
                # create dictionary of column-name:field-value
                if headers[i] == 'birthday':
                    item = datetime.strptime(item, '%b %d, %Y').date()
                values.update({headers[i]: item})
            # validate the row
            try:
                schema(values)
            except MultipleInvalid as e:
                print(e)
                values['valid'] = False
                values['failures'] = str(e)
            # create database record
            order = Order(**values)
            db.session.add(order)
        db.session.commit()
        return {'success':True}


# Routes
api.add_resource(Orders, '/')

    

if __name__ == '__main__':
    app.run()
