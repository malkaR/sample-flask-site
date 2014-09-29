import csv
import sys, os 
import json
from datetime import datetime

from flask import request, make_response
from flask.ext.restful import abort, Resource, fields, marshal, reqparse
from voluptuous import Schema, Required, All, Length, Range, Error, MultipleInvalid, Invalid, Any, Match, In

sys.path.append(os.path.abspath(os.pardir))
from api.config.validation_constants import DATE_FORMAT, US_STATES
from api.validation.formatter import create_schema_from_config

# global fields - these can't be imported yet to prevent circular imports
global db, Order, schema, dependent_schema, order_fields, fields_list

def get_imports():
    """import at runtime to prevent circular imports"""
    global db, Order, schema, dependent_schema, order_fields, fields_list
    from flaskr import db, schema, dependent_schema, order_fields
    from models import Order, fields_list

# Fields and their types for JSON Responses
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

# Orders resource parser
parser = reqparse.RequestParser()
arg_kwargs = dict(location='args', default=None)
parser.add_argument('valid', type=int, choices=BOOLEAN_CHOICES, help='the parameter value for valid must be either 1 or 0',  **arg_kwargs)
parser.add_argument('state', type=str, choices=US_STATES, help='the parameter value for state must be an uppercase abbreviated US state', **arg_kwargs)
parser.add_argument('zipcode', type=int, help='the parameter value for zipcode must be a number', **arg_kwargs)


class Orders(Resource):

    def get(self):
        """
        Returns the list of orders. Filter by any of the valid, state, or zipcode arguments.
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
        """Return the full details of a given order"""
        get_imports()
        return marshal(db.session.query(Order).filter_by(id=order_id).first(), full_resource_fields)


class OrderImport(Resource):

    def add_to_error_list(self, values, field_name, error):
        """Add the error_message to the list of errors"""
        if 'errors' in values and values['errors']:
            values['errors'].append({"field":field_name, "errors":error.error_message})
        else:
            values['errors'] = [{"field":field_name, "errors":error.error_message}]

    def put(self):
        """Insert new orders from the csv data provided in the data parameter."""
        get_imports()
        try:
            lines = request.form['data']
        except KeyError:
            abort(400, message='Param `data` is required to insert orders')
        if '|' not in lines:
            abort(400, message='Expected csv data to be separated with `|`.')
        try:
            csvreader = csv.reader(lines.split('\\n'), delimiter='|')
        except Exception as e:
            abort(400, message='Error found in reading data as `|` separated csv data. Error is: %s' % str(e))
        
        headers = csvreader.next()
        ids_inserted_updated = []

        for row in csvreader:

            values = {'valid':True, 'errors':None}
            for i, item in enumerate(row):
                # create dictionary of column-name:field-value
                values.update({headers[i]: item})
            
            # validate the whole row first
            try:
                values = schema(values)
            except MultipleInvalid as e:
                # errors were found, loop through keys to validate and get the value to store and the errors for individual fields
                
                # validate the required fields first
                for field_name in schema.schema.keys():
                    if str(field_name) in order_fields['order_fields_validators']['required_fields'].keys():
                        
                        field_name = str(field_name)
                        field_schema = create_schema_from_config({field_name:order_fields['order_fields_validators']['required_fields'][field_name]})
                 
                        try:
                            values.update(field_schema({field_name:values[field_name]}))
                        except KeyError:
                            # a required field is not present, abort
                            abort(400, message='missing `%s` which is a required field' % field_name)
                        except MultipleInvalid as e:
                            # a required field does not validate, abort
                            abort(400, message='problem validating required field `%s`, error message is: %s' % (field_name, e.errors[0].error_message))
                
                # now validate the optional fields
                for field_name in schema.schema.keys():
                    if field_name in order_fields['order_fields_validators']['optional_fields'].keys():
                        
                        field_schema = create_schema_from_config({field_name:order_fields['order_fields_validators']['optional_fields'][field_name]})
                        
                        try:
                            values.update(field_schema({field_name:values[field_name]}))
                        except MultipleInvalid as e:
                            
                            values['valid'] = False
                            
                            # loops through each field in the schema that raised errors
                            for error in e.errors: 
                                self.add_to_error_list(values, field_name, error)

                                # check if the field requires a default when validation to coerce it fails
                                if error.path and len(error.path) == 1:
                                    order_fields_defaults = order_fields['order_fields_defaults']

                                    if field_name in order_fields_defaults:
                                        # this is a field that requires a replacement value 
                                        if order_fields_defaults[field_name]['coerce_failure_msg'] == error.error_message:
                                            # the error message corresponds to the coercion error message, update with replacement value
                                            values[field_name] = order_fields_defaults[field_name]['failure_value']
                                        else:
                                            # the coercion was successul but another validation requirement failed.
                                            # coerce again to avoid database Type Errors upon insertion
                                            coerce_schema = create_schema_from_config({field_name:{
                                                            'functions':{
                                                                'CoerceTo':
                                                                    order_fields['order_fields_validators']['optional_fields'][field_name]['functions']['CoerceTo']
                                                            }}})
                                            values.update(coerce_schema({field_name:values[field_name]}))
                    else:
                        pass
                        # field name not in schema at all, a future implementation would add the database field here
            
            # validation that depends on more than one field
            if dependent_schema:
                
                try:
                    dependent_schema(values)
                except MultipleInvalid as e:
                    values['valid'] = False
                    for error in e.errors:
                        self.add_to_error_list(values, 'multiple fields', error)
            
            # validation is complete, now do some prep and then add the record to the db session
            if 'errors' in values and values['errors']:
                values['errors'] = json.dumps(values['errors'])
            order = Order(**values)
            db.session.merge(order)
            ids_inserted_updated.append(order.id)

        db.session.commit()
        return {"results": marshal(db.session.query(Order).filter(Order.id.in_(ids_inserted_updated)).all(), full_resource_fields)}, 201 #

