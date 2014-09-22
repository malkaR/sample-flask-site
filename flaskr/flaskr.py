import sqlite3
import us
import csv
import copy
import os
import yaml
# import json
from flask import Flask, g, request, make_response
from flask.ext.restful import abort, Api, Resource, fields, marshal, reqparse
from flask.ext.sqlalchemy import SQLAlchemy
from voluptuous import Schema, Required, All, Length, Range, Invalid, MultipleInvalid
from datetime import datetime, date

app = Flask(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
api = Api(app)
db = SQLAlchemy(app)
US_STATES = [state.abbr for state in us.states.STATES]
DATE_FORMAT = '%b %d, %Y'
# US_STATES_ICASE = US_STATES + [state.lower() for state in US_STATES]

order_fields_file = open('/Users/malka/Documents/job/Lot18Code/flaskr/config/field_validators.yaml')
# use safe_load instead load
order_fields = yaml.safe_load(order_fields_file)
order_fields_file.close()

# print order_fields

def forbidden_values(values_list=[], column_name=None):
    """
    The field's value can not be one of the values_list items.
    """
    def f(v):
        if v in values_list:
            msg = 'Value: {}; Error: This is not an allowed value'.format(v)
            if column_name:
                msg = 'Field: {}; '.format(column_name) + msg
            raise Invalid(msg)
        return v

    return f

def coerce_to_type(typ=int, column_name=None):
    if type(typ) == str:
        typ = eval(typ)

    def f(v):
        try:
            return typ(v)
        except ValueError as e:
            msg = 'Value: {}; Error: can not be converted to the {} type'.format(str(v), typ)
            if column_name:
                msg = 'Field: {}; '.format(column_name) + msg
            raise Invalid(msg)
    return f

class Struct:
    def __init__(self, **entries):
        self.schema = {}
        self.__dict__.update(entries)
        if not hasattr(self, 'required_fields'):
            self.__dict__.update({'required_fields':{}})
        else:
            self.complete_required_field_dictionaries(self.required_fields)

        if not hasattr(self, 'optional_fields'):
            self.__dict__.update({'optional_fields':{}})
        else:
            self.complete_optional_field_dictionaries(self.optional_fields)
        

    def complete_required_field_dictionaries(self, required_field_dict):
        for field_name, field_validators in required_field_dict.items():
            self.schema[Required(field_name)] = self.get_field_validators(field_validators)

    def complete_optional_field_dictionaries(self, optional_field_dict):
        for field_name, field_validators in optional_field_dict.items():
            self.schema[field_name] = self.get_field_validators(field_validators)
    
    def get_field_validators(self, field_validators):
            args = []
            if 'type' in field_validators:
                args.append(eval(field_validators['type']))
            if 'functions' in field_validators:
                for function_name, function_args in field_validators['functions'].items():
                    # if type(function_name) == str:
                    #     args.append(eval(function_name)())
                    # else:
                    args.append(eval(function_name)(*tuple(function_args.get('args', [])), **function_args.get('kwargs', {})))
            if len(args) > 1:
                return All(*tuple(args))
            return args[0]
    
    def get_schema(self):
        return self.schema

    def __repr__(self):
        return str(self.__dict__)


def create_schema_from_config(config_dict):
    schema_dict = Struct(**config_dict['order_fields'])
    schema = Schema(schema_dict.schema)
    return schema


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




# schema = Schema({
#     Required('id'): All(coerce_to_type(int, column_name='order_id'),),
#     Required('name'): All(str, Length(min=1)),
#     'email': str,
#     'birthday' : date,
#     'state': All(str, forbidden_values(values_list=['NJ', 'CT', 'PA', 'MA', 'OR', 'ID', 'IL'], column_name='state')),
#     'zipcode': str
# })

schema = create_schema_from_config(order_fields)

class OrderImport(Resource):
    def get(self):
        return {'hello': 'world'}

    def put(self):
        lines = request.form['data'].split('\\n') #TODO: tell user that param is called data with reqparse
        csvreader = csv.reader(lines, delimiter='|')
        headers = csvreader.next()
        values = {}
        for row in csvreader:
            for i, item in enumerate(row):
                # create dictionary of column-name:field-value
                if headers[i] == 'birthday':
                    item = datetime.strptime(item, DATE_FORMAT).date()
                values.update({headers[i]: item})
            # validate the row
            try:
                schema(values)
            except MultipleInvalid as e:
                values['valid'] = False
                values['failures'] = str(e)
            # create database record
            order = Order(**values)
            db.session.add(order)
        db.session.commit()
        return {'success':True}



basic_resource_fields = {
    'id':       fields.Integer,
    'name':     fields.String,
    'valid':    fields.Boolean
}

class DateField(fields.Raw):
    def format(self, value):
        return datetime.strftime(value, DATE_FORMAT)

full_resource_fields = {
    'email':    fields.String,
    'birthday': DateField,
    'state':    fields.String,
    'zipcode':  fields.Integer,
    'failures': fields.String
}

full_resource_fields.update(basic_resource_fields)

BOOLEAN_CHOICES = ['0', '1']

parser = reqparse.RequestParser()
arg_kwargs = dict(location='args', default=None)
parser.add_argument('valid', type=int, choices=BOOLEAN_CHOICES, help='the parameter value for valid must be either 1 or 0',  **arg_kwargs)
parser.add_argument('state', type=str, choices=US_STATES, help='the parameter value for state must be an uppercase abbreviated US state', **arg_kwargs)
parser.add_argument('zipcode', type=int, help='the parameter value for zipcode must be a number', **arg_kwargs)
# parser.add_argument('name', type=str)


class Orders(Resource):

    def get(self):
        """
        Returns the list of orders.
        For example:
        {"results": [{"order_id": 4453, 
                      "name": "Guido van Rossum", 
                      "valid": true}]}
        """
        args = parser.parse_args()
        filter_kwargs = {}
        for arg in 'valid state zipcode'.split():
            if args[arg] != None:
                filter_kwargs.update({arg:args[arg]})
        return {"results": marshal(db.session.query(Order).filter_by(**filter_kwargs).all(), basic_resource_fields)}

class FullOrder(Resource):

    def get(self, order_id):
        return marshal(db.session.query(Order).filter_by(id=order_id).first(), full_resource_fields)

# Routes
api.add_resource(OrderImport, '/orders/import')
api.add_resource(Orders, '/orders')
api.add_resource(FullOrder, '/orders/<string:order_id>')

    

if __name__ == '__main__':
    app.run()
