
from flask import request, make_response
from flask.ext.restful import abort, Resource, fields, marshal, reqparse


from voluptuous import Schema, Required, All, Length, Range, Error, MultipleInvalid, Invalid, Any, Match, In
import csv
import sys, os 
import json

sys.path.append(os.path.abspath(os.pardir))
global db, Order, schema, dependent_schema, order_fields


from api.config.validation_constants import DATE_FORMAT, US_STATES
from api.validation.formatter import create_schema_from_config

from datetime import datetime

class DateField(fields.Raw):
    def format(self, value):
        return datetime.strftime(value, DATE_FORMAT)

class JSONString(fields.String):
    def format(self, value):
        return json.loads(value)

basic_resource_fields = {
    'id':       fields.Integer,
    'name':     fields.String,
    'valid':    fields.Boolean
}

full_resource_fields = {
    'email':    fields.String,
    'birthday': DateField,
    'state':    fields.String,
    'zipcode':  fields.Integer,
    'errors': JSONString
}

full_resource_fields.update(basic_resource_fields)

BOOLEAN_CHOICES = ['0', '1']

parser = reqparse.RequestParser()
arg_kwargs = dict(location='args', default=None)
parser.add_argument('valid', type=int, choices=BOOLEAN_CHOICES, help='the parameter value for valid must be either 1 or 0',  **arg_kwargs)
parser.add_argument('state', type=str, choices=US_STATES, help='the parameter value for state must be an uppercase abbreviated US state', **arg_kwargs)
parser.add_argument('zipcode', type=int, help='the parameter value for zipcode must be a number', **arg_kwargs)

def get_imports():
    global db, Order, schema, dependent_schema, order_fields
    from flaskr import db, schema, dependent_schema, order_fields
    from models import Order


class Orders(Resource):

    def get(self):
        """
        Returns the list of orders.
        For example:
        {"results": [{"order_id": 4453, 
                      "name": "Guido van Rossum", 
                      "valid": true}]}
        """
        get_imports()
        args = parser.parse_args()
        filter_kwargs = {}
        for arg in 'valid state zipcode'.split():
            if args[arg] != None:
                filter_kwargs.update({arg:args[arg]})
        return {"results": marshal(db.session.query(Order).filter_by(**filter_kwargs).all(), basic_resource_fields)}

class FullOrder(Resource):

    def get(self, order_id):
        get_imports()
        return marshal(db.session.query(Order).filter_by(id=order_id).first(), full_resource_fields)


class OrderImport(Resource):
    def get(self):
        get_imports()
        return {'hello': 'world'}

    def add_to_error_list(self, values, field_name, error):
        if 'errors' in values and values['errors']:
            values['errors'].append({"field":field_name, "errors":error.error_message})
        else:
            values['errors'] = [{"field":field_name, "errors":error.error_message}]


    def put(self):
        get_imports()
        lines = request.form['data'].split('\\n') #TODO: tell user that param is called data with reqparse
        csvreader = csv.reader(lines, delimiter='|')
        headers = csvreader.next()
        
        for row in csvreader:
            values = {'valid':True, 'errors':None}
            for i, item in enumerate(row):
                # create dictionary of column-name:field-value
                values.update({headers[i]: item})

            # validate the row
            try:
                values = schema(values)
            except MultipleInvalid as e:
                
                # errors were found, loop through keys to get the correct value and the errors for individual fields
                for field_name in schema.schema.keys():

                    if str(field_name) in order_fields['order_fields_validators']['required_fields'].keys():
                        field_name = str(field_name)
                        # required field errors
                         
                        field_schema = create_schema_from_config({field_name:order_fields['order_fields_validators']['required_fields'][field_name]})
                 
                        try:
                            values.update(field_schema({field_name:values[field_name]}))
                        except MultipleInvalid as e:
                            print 'problem again', e
                            abort('problem validating')
                    elif field_name in order_fields['order_fields_validators']['optional_fields'].keys():
                        # optional field errors
                        field_schema = create_schema_from_config({field_name:order_fields['order_fields_validators']['optional_fields'][field_name]})
                        try:
                            values.update(field_schema({field_name:values[field_name]}))
                        except MultipleInvalid as e:

                
                            
                            values['valid'] = False
                            
                            for error in e.errors: # loops through each field in the schema that raised errors
                                
                                self.add_to_error_list(values, field_name, error)

                                if error.path and len(error.path) == 1:
                                    order_fields_defaults = order_fields['order_fields_defaults']
                                    if field_name in order_fields_defaults:
                                        # this is a field that requires a replacement value if type/format coercion fails
                                        if order_fields_defaults[field_name]['coerce_failure_msg'] == error.error_message:
                                            # the error message corresponds to the coercion error message, update with replacement value
                                            values[field_name] = order_fields_defaults[field_name]['failure_value']
                                        else:
                                            # the coercion was successul but another validation requirement failed.
                                            # coerce again to avoid database Type Errors
                                            coerce_schema = create_schema_from_config({field_name:{'functions':{'CoerceTo':order_fields['order_fields_validators']['optional_fields'][field_name]['functions']['CoerceTo']}}})
                                            
                                            values.update(coerce_schema({field_name:values[field_name]}))
                    else:
                        pass
                        # field name not in schema at all
            if dependent_schema:
                try:
                    dependent_schema(values)
                except MultipleInvalid as e:
                    values['valid'] = False
                    for error in e.errors:
                        self.add_to_error_list(values, 'multiple fields', error)
            
            if 'errors' in values and values['errors']:
                values['errors'] = json.dumps(values['errors'])
                
            # create database record
            order = Order(**values)
            db.session.merge(order)
        db.session.commit()
        return {'success':True}

