import sqlite3
import us
import csv
import copy
import os
import yaml
from flask import Flask, g, request, make_response
from flask.ext.restful import abort, Api, Resource, fields, marshal, reqparse
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime, date
from functools import wraps
import sys
from validate_email import validate_email

app = Flask(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
api = Api(app)
db = SQLAlchemy(app)
US_STATES = [state.abbr for state in us.states.STATES]
STATES_LESS_NY = [str(state.abbr) for state in us.states.STATES if state.abbr != 'NY']


sys.path.append(os.path.abspath(os.pardir))
from voluptuous import Schema, Required, All, Length, Range, Error, MultipleInvalid, Invalid, Any, Match, In

# validation error messages
DATE_FORMAT = '%b %d, %Y'
LENGTH_CHOICE_ERROR = 'length must be valid, choose from {}'
LENGTH_RANGE_ERROR = 'length must be valide, between {} and {}'
SUM_MAX_ERROR = 'sum of values must be no more than {}'
FORBIDDEN_VALUE_ERROR = 'the value is not allowed, do not choose from {}'
AT_MOST_DATE_RANGE_ERROR = 'value must be at most {}'
LOWER_THAN_DATE_RANGE_ERROR = 'value must be lower than {}'
HIGHER_THAN_DATE_RANGE_ERROR = 'value must be higher than {}'
AT_LEAST_DATE_RANGE_ERROR = 'value must be at least {}'
COERCE_DATE_ERROR = 'value does not represent a valid date, the date format must follow {}'.format(DATE_FORMAT)
COERCE_INT_ERROR = 'value does not represent an integer'
INVALID_EMAIL_ERROR = 'email address is not valid'
NY_EMAIL_ERROR = 'NY email address can not belong to a .net domain'
MISSING_ENDING_ERROR = 'the value must end with {}'
UNALLOWED_ENDING_ERROR = 'the value can not end with {}'
today = date.today()
ZIPCODE_LENGTHS = [5, 9]
LENGTH_CHOICE_ERROR_ZIPCODE = LENGTH_CHOICE_ERROR.format(ZIPCODE_LENGTHS)
# validation constants
validate_with = {
    'TODAY_LESS_21_YEARS': date(year=today.year - 21, month = today.month, day=today.day),
    'FORBIDDEN_STATES': ['NJ', 'CT', 'PA', 'MA', 'OR', 'ID', 'IL'],
    'ZIPCODE_LENGTHS': ZIPCODE_LENGTHS,
    'LENGTH_CHOICE_ERROR_ZIPCODE': LENGTH_CHOICE_ERROR_ZIPCODE,
    # 'MAX_EMAIL_SUM': 20,
    'COERCE_DATE_ERROR': COERCE_DATE_ERROR,
    'LENGTH_CHOICE_ERROR': LENGTH_CHOICE_ERROR,
    'LENGTH_RANGE_ERROR': LENGTH_RANGE_ERROR,
    'FORBIDDEN_VALUE_ERROR': FORBIDDEN_VALUE_ERROR,
    'AT_MOST_DATE_RANGE_ERROR': AT_MOST_DATE_RANGE_ERROR,
    'LOWER_THAN_DATE_RANGE_ERROR': LOWER_THAN_DATE_RANGE_ERROR,
    'HIGHER_THAN_DATE_RANGE_ERROR': HIGHER_THAN_DATE_RANGE_ERROR,
    'AT_LEAST_DATE_RANGE_ERROR': AT_LEAST_DATE_RANGE_ERROR,
    'COERCE_INT_ERROR': COERCE_INT_ERROR,
    'INVALID_EMAIL_ERROR': INVALID_EMAIL_ERROR,
    'SUM_MAX_ERROR': SUM_MAX_ERROR,
    'STATES_LESS_NY': STATES_LESS_NY,
    'NY_EMAIL_ERROR': NY_EMAIL_ERROR
}
# parse yaml validators
order_fields_file = open('/Users/malka/Documents/job/Lot18Code/flaskr/config/field_validators.yaml')
from string import Template
s = Template(order_fields_file.read())
s = s.substitute(**validate_with)
# use safe_load instead load
order_fields = yaml.load(s)
order_fields_file.close()
order_fields_defaults = order_fields['order_fields_defaults']

def get_base_error_message(error):
    if not isinstance(error, unicode):
        return None
    try:
        error_msg = eval(error).split('{}')
    except NameError:
        return None
    try:
        error_msg.remove('')
    except ValueError:
        pass
    error_msg = ''.join(error_msg)
    return error_msg

def convert_to_date(v):
    return datetime.strptime(v, DATE_FORMAT).date()

def DateRange(min=None, max=None, min_included=True, max_included=True, msg=None):

    def f(v):
        if not isinstance(v, date):
            try:
                v = convert_to_date(v)
            except Exception as e:
                raise Invalid(str(e))

        if min_included:
            if min is not None and v < min:
                raise Invalid(msg or AT_LEAST_DATE_RANGE_ERROR.format(min))
        else:
            if min is not None and v <= min:
                raise Invalid(msg or HIGHER_THAN_DATE_RANGE_ERROR.format(min))
        if max_included:
            if max is not None and v > max:
                raise Invalid(msg or AT_MOST_DATE_RANGE_ERROR.format(max))
        else:
            if max is not None and v >= max:
                raise Invalid(msg or LOWER_THAN_DATE_RANGE_ERROR.format(max))
        return v
    return f

def MatchesEmailRegEx(msg=None, column_name='email'):
    if msg == None:
        msg = INVALID_EMAIL_ERROR

    def f(v):
        if validate_email(v):
            return v
        raise Invalid(msg)

    return f

def EndsWith(ending, allowed=True, msg=None):

    if msg == None:
        if allowed:
            msg = MISSING_ENDING_ERROR.format(ending)
        else:
            msg = UNALLOWED_ENDING_ERROR.format(ending)

    def f(v):
        if (v[-len(ending):] == ending and allowed) or (v[-len(ending):] != ending and not allowed):
            return v
        raise Invalid(msg)

    return f



def ValueNotIn(container, msg=None, column_name=None):
    """
    The field's value can not be one of the container items.
    """
    if msg == None:
        msg = FORBIDDEN_VALUE_ERROR.format(container)
  
    def f(v):
        if v in container:
            raise Invalid(msg)
        return v

    return f

def LengthCustom(min=None, max=None, msg=None):
    if msg == None:
        msg = LENGTH_RANGE_ERROR.format(min or 'any', max or 'any')

    return Length(min=min, max=max, msg=msg)

def LengthIn(container, msg=None, column_name=None):
    """Validate that the length of the value or the string representation of the value is in the collection of integers."""
    if msg == None:
        msg = LENGTH_CHOICE_ERROR.format(container)

    def validator(value):
        try:
            if len(value) in container:
                return value
        except TypeError:
            try:
                if len(str(value)) in container:
                    return value
            except Exception:
                pass
        raise Invalid(msg)

    return validator

def SumMax(max_sum, msg=None, column_name=None):
    """
    The individual integers in the field can not sum to more than `max_sum`.
    The field must be an integer or string that reprsents an integer.
    """
    if msg == None:
        msg = SUM_MAX_ERROR.format(max_sum)

    def f(v):
        if sum(int(i) for i in str(v)) > 20:
            raise Invalid(msg)
        return v

    return f


def CoerceTo(typ=None, column_name=None, converter_function=None, msg=None, return_original=False):
    if type(typ) == str:
        typ = eval(typ)
    if converter_function:
        converter_function = eval(converter_function)

    if not msg:
        msg = 'Can not convert value with the {} type or function'.format(typ or converter_function)
    # TODO: need one of typ or converte_function, else invalid schema
    def f(v):
        # if the value is already the correct type then just return it
        if typ and isinstance(v, typ):
            return v
        elif converter_function:
            # convert with the custom function if one is provided
            if converter_function: 
                try:
                    converted_value = converter_function(v)
                    if return_original:
                        return v
                    return converted_value
                except Exception as e:
                    raise Invalid(msg)
        elif typ:
            # convert by type-casting
            try:
                converted_value = typ(v)
                if return_original:
                    return v
                return converted_value
            except ValueError as e:
                
                raise Invalid(msg)
        
    return f

class Struct:
    def __init__(self, **entries):
        self.schema = {}
        self.dependent_schema = {}
        self.args = []
        self.__dict__.update(entries)
        if not hasattr(self, 'required_fields'):
            self.__dict__.update({'required_fields':{}})
        else:
            self.complete_required_field_dictionaries(self.required_fields)

        if not hasattr(self, 'optional_fields'):
            self.__dict__.update({'optional_fields':{}})
        else:
            self.complete_optional_field_dictionaries(self.optional_fields)

        if not hasattr(self, 'dependent_fields'):
            self.__dict__.update({'dependent_fields': {}})
        else:
            self.complete_dependent_fields_dictionaries(self.dependent_fields)

        if not self.optional_fields and not self.required_fields:
            # simplest schema type for one field
            self.complete_optional_field_dictionaries(entries)



    def complete_required_field_dictionaries(self, required_field_dict):
        for field_name, field_validators in required_field_dict.items():
            self.schema[Required(field_name)] = self.create_schema_from_args(self.get_field_validators(field_validators))

    def complete_optional_field_dictionaries(self, optional_field_dict):
        for field_name, field_validators in optional_field_dict.items():
            self.schema[field_name] = self.create_schema_from_args(self.get_field_validators(field_validators))

    def complete_dependent_fields_dictionaries(self, dependent_fields_dict):
        qualifier = eval(dependent_fields_dict['qualifier'])
        msg = dependent_fields_dict['msg'] if 'msg' in dependent_fields_dict else None
        and_dictionary = {}
        or_list = []

        def evaluate_or(or_dict):
            or_field_schema = {}
            if 'And' in or_dict:
                or_list.append(evaluate_and(or_dict['And']))
            for item in or_dict:
                if item not in ['Or', 'And']:
                    or_field_schema[item] = self.get_field_validators(or_dict[item])[0]
            or_list.append(or_field_schema)
            return or_list

        def evaluate_and(and_dict):
            and_field_schema = {}
            if 'Or' in and_dict:
                and_dictionary.update(evaluate_or(and_dict['Or']))
        
            for item in and_dict:
                if item not in ['Or', 'And']:
                    and_field_schema[item] = self.get_field_validators(and_dict[item])[0]
            and_dictionary.update(and_field_schema)
            return and_dictionary


        top_level_args = top_level_dict = None
        top_level_fields = {}
        if 'Or' in dependent_fields_dict:
            top_level_args = evaluate_or(dependent_fields_dict['Or'])
                  

        elif 'And' in dependent_fields_dict:
            top_level_dict = evaluate_and(dependent_fields_dict['And'])

        for item in dependent_fields_dict:
            if item not in ['Or', 'And', 'qualifier', 'msg']:
                top_level_fields[item] = self.get_field_validators(dependent_fields_dict[item])[0]

        if top_level_args:
            # top level is Or
            self.dependent_schema = self.create_schema_from_args(top_level_args, qualifier=qualifier, msg=msg, extra=True)
        elif top_level_dict:
            self.dependent_schema = self.create_schema_from_args([top_level_dict], qualifier=qualifier, msg=msg, extra=True)
            
    def get_field_validators(self, field_validators):
        args = []
        if 'type' in field_validators:
            args.append(eval(field_validators['type']))
        if 'value' in field_validators:
            args.append(field_validators['value'])
        if 'functions' in field_validators:
            if 'functions_order' in field_validators:
                for function_name in field_validators['functions_order']:
                    function_args = field_validators['functions'][function_name]
                    args.append(eval(function_name)(*tuple(function_args.get('args', [])), **function_args.get('kwargs', {})))
            else:
                for function_name, function_args in field_validators['functions'].items():
                    args.append(eval(function_name)(*tuple(function_args.get('args', [])), **function_args.get('kwargs', {})))
        return args
            
    def create_schema_from_args(self, args, qualifier=All, **kwargs):
        if len(args) > 1:
            return qualifier(*tuple(args), **kwargs)
        return args[0]
    
    def get_schema(self):
        return self.schema

    def get_dependent_schema(self):
        return self.dependent_schema

    def __repr__(self):
        return str(self.__dict__)


def create_schema_from_config(config_dict, simple=True):
    schema_dict = Struct(**config_dict)
    if simple:
        return Schema(schema_dict.get_schema())
    return [Schema(schema_dict.get_schema(), extra=True), Schema(schema_dict.get_dependent_schema())]


# Database Model
class Order(db.Model):
    __tablename__ =  'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), nullable=True)
    birthday = db.Column(db.Date, nullable=True)
    state = db.Column(db.String(2), nullable=True)
    zipcode = db.Column(db.String(9), nullable=True)

    valid = db.Column(db.Boolean, default=True)
    errors = db.Column(db.Text, nullable=True)

    def __init__(self, *args, **kwargs):
        for field in kwargs:
            setattr(self, field, kwargs[field])

    def __repr__(self):
        return '<Order %d>' % self.id

# Order validation 


schema, dependent_schema = create_schema_from_config(order_fields['order_fields_validators'], simple=False)

class OrderImport(Resource):
    def get(self):
        return {'hello': 'world'}

    def put(self):
        lines = request.form['data'].split('\\n') #TODO: tell user that param is called data with reqparse
        csvreader = csv.reader(lines, delimiter='|')
        headers = csvreader.next()
        values = {}
        values['errors'] = []
        for row in csvreader:
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
                        
                                if values['errors']:
                                    values['errors'].append({'field':field_name, 'errors':error.error_message})
                                else:
                                    values['errors'] = [{'field':field_name, 'errors':error.error_message}]

                                if error.path and len(error.path) == 1:
                                    
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
                    values['errors'] = list(values['errors'])
                    for error in e.errors:
                        values['errors'].append({'field':'multiple fields', 'errors':error.error_message})
                    #     values.update({error.path[0]:None})
            
            if values['errors']:    
                values['errors'] = str(values['errors'])
            else:
                values['errors'] = None
                
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
    'errors': fields.String
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
