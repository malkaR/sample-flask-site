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
from datetime import datetime, date
from functools import wraps
import sys

app = Flask(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
api = Api(app)
db = SQLAlchemy(app)
US_STATES = [state.abbr for state in us.states.STATES]
DATE_FORMAT = '%b %d, %Y'
# US_STATES_ICASE = US_STATES + [state.lower() for state in US_STATES]


sys.path.append(os.path.abspath(os.pardir))
from voluptuous import Schema, Required, All, Length, Range, Error, MultipleInvalid, Invalid

# validation error messages
LENGTH_ERRROR = 'length must be valid, choose from {}'
FORBIDDEN_VALUE_ERROR = 'the value is not allowed, do not choose from {}'
AT_MOST_DATE_RANGE_ERROR = 'value must be at most {}'
LOWER_THAN_DATE_RANGE_ERROR = 'value must be lower than {}'
HIGHER_THAN_DATE_RANGE_ERROR = 'value must be higher than {}'
AT_LEAST_DATE_RANGE_ERROR = 'value must be at least {}'
COERCE_DATE_ERROR = 'value does not represent a valid date, the date format must follow {}'.format(DATE_FORMAT)

today = date.today()


# validation constants
validate_with = {
    'TODAY_LESS_21_YEARS': date(year=today.year - 21, month = today.month, day=today.day),
    'FORBIDDEN_STATES': ['NJ', 'CT', 'PA', 'MA', 'OR', 'ID', 'IL'],
    'ZIPCODE_LENGTHS': [5, 9],
    'COERCE_DATE_ERROR': COERCE_DATE_ERROR,
    'LENGTH_ERRROR': LENGTH_ERRROR,
    'FORBIDDEN_VALUE_ERROR': FORBIDDEN_VALUE_ERROR,
    'AT_MOST_DATE_RANGE_ERROR': AT_MOST_DATE_RANGE_ERROR,
    'LOWER_THAN_DATE_RANGE_ERROR': LOWER_THAN_DATE_RANGE_ERROR,
    'HIGHER_THAN_DATE_RANGE_ERROR': HIGHER_THAN_DATE_RANGE_ERROR,
    'AT_LEAST_DATE_RANGE_ERROR': AT_LEAST_DATE_RANGE_ERROR
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
    if not isinstance(error, str):
        return ''
    try:
        error_msg = eval(error).split('{}')
    except NameError:
        return ''
    error_msg.remove('')
    error_msg = ''.join(error_msg)
    return error_msg

def convert_to_date(v):
    return datetime.strptime(v, DATE_FORMAT).date()

def DateRange(min=None, max=None, min_included=True, max_included=True, msg=None):

    def f(v):
        print 'checking date range', v
        if not isinstance(v, date):
            print 'did not find date'
            print type(v)
            try:
                v = convert_to_date(v)
            except Exception as e:
                raise Invalid(str(e))

        if min and not isinstance(min, date):
            raise Invalid('problem converting min or max to date')
        if max and not isinstance(max, date):
            raise Invalid('problem converting min or max to date')


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

def LengthIn(container, msg=None, column_name=None):
    """Validate that the length of value is in a collection."""

    if msg == None:
        msg = LENGTH_ERRROR.format(container)
        if column_name != None:
            msg = '{} {}'.format(column_name, msg)

    def validator(value):
        if not len(value) in container:
            raise Invalid(msg)
        return value
    return validator



# class Invalid(Error):
#     """The data was invalid.

#     :attr msg: The error message.
#     :attr path: The path to the error, as a list of keys in the source data.
#     :attr error_message: The actual error message that was raised, as a
#         string.

#     """

#     def __init__(self, message, path=None, error_message=None, nullify=False):
#         Error.__init__(self,  message)
#         self.path = path or []
#         self.error_message = error_message or message
#         self.nullify = nullify

#     @property
#     def msg(self):
#         return self.args[0]

#     def __str__(self):
#         path = ' @ data[%s]' % ']['.join(map(repr, self.path)) \
#             if self.path else ''
#         return Exception.__str__(self) + path

# import voluptuous
# voluptuous.Invalid = Invalid
# class InvalidAndReplace(Invalid):

#     def __init__(self, msg, path=None, error_message=None, nullify=False):
#         super(InvalidAndReplace, self).__init__(str(msg), path=None, error_message=None)
#         print 'initiating InvalidAndReplace, nullify is ', nullify
#         self.nullify = nullify

#     def __repr__(self):
#         return 'InvalidAndReplace <nullify:(%s)>' % self.nullify






# def All(*validators, **kwargs):
#     """Value must pass all validators.

#     The output of each validator is passed as input to the next.
#     All validators are evaluated even if earlier ones failed.

#     :param msg: Message to deliver to user if validation fails.
#     :param kwargs: All other keyword arguments are passed to the sub-Schema constructors.

#     >>> validate = Schema(All('10', Coerce(int)))
#     >>> validate('10')
#     10
#     """
#     msg = kwargs.pop('msg', None)
#     replace_on_failure = kwargs.pop('replace_on_failure', False)
#     schemas = [Schema(val, **kwargs) for val in validators]
    
#     def validate(v):
#         global current_v
#         current_v = v
#         for schema in schemas:
#             try:
#                 current_v = schema(current_v)
#             except Invalid as e:
#                 yield e if msg is None else Invalid(msg)
        

#     def f(v):
#         global current_v
#         errors = list(validate(v))
#         if errors:
#             replace = False

#             if v != current_v and replace_on_failure:
#                 print 'sending kwarg to replace'
#                 replace = True
#             raise MultipleInvalidForField(errors, replace=replace, last_value=current_v)
            
#         return v

#     return f

# def CoerceOrNullify(typ=int, column_name=None, converter_function=None):
#     if type(typ) == str:
#         typ = eval(typ)
#     if converter_function:
#         converter_function = eval(converter_function)
    
#     def f(v):
#         print 'coerce or nullify fx', v
#         # if the value is already the correct type then just return it
#         if isinstance(v, typ):
#             return v
#         # convert with the custom function if one is provided
#         if converter_function: 
#             try:
#                 return converter_function(v)
#             except Exception as e:
#                 print 'returning none'
#                 return None
#         # convert by type-casting
#         try:
#             return typ(v)
#         except ValueError as e:
#             print 'returning none'
#             return None
#     return f

# def Replace(typ=None, column_name=None, converter_function=None, nullify_on_failure=False, replacement_on_failurement=None):
#     """Replace a value if it can not be coerced to the correct type or format."""
#     if typ != None and type(typ) == str:
#         typ = eval(typ)
#     if converter_function:
#         converter_function = eval(converter_function)
    
#     def return_replacement():
#         if nullify_on_failure:
#             return None
#         if replacement_on_failurement:
#             return replacement_on_failurement

#     def f(v):
#         print 'coerce or replace', v
#         # if the value is already the correct type then just return it
#         if typ != None and isinstance(v, typ):
#             return v
#         # convert with the custom function if one is provided
#         if converter_function: 
#             try:
#                 return converter_function(v)
#             except Exception as e:
#                 return_replacement()
#         # convert by type-casting
#         if typ != None:
#             try:
#                 return typ(v)
#             except ValueError as e:
#                 return_replacement()
#     return f



def CoerceTo(typ=None, column_name=None, converter_function=None, msg=None):
    if type(typ) == str:
        typ = eval(typ)
    if converter_function:
        converter_function = eval(converter_function)
    
    # TODO: need one of typ or converte_function, else invalid schema
    def f(v):
        print 'coercing', v
        # if the value is already the correct type then just return it
        if typ and isinstance(v, typ):
            return v
        elif typ:
            # convert by type-casting
            try:
                return typ(v)
            except ValueError as e:
                if not msg:
                    msg = 'Value: {}; Error: can not be converted with the {} type or function'.format(str(v), typ or converter_function)
                if column_name:
                    msg = 'Field: {}; '.format(column_name) + msg
                raise Invalid(msg)
        elif converter_function:
            # convert with the custom function if one is provided
            if converter_function: 
                try:
                    return converter_function(v)
                except Exception as e:
                    raise Invalid(str(e)) # TODO
        
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

        if not self.optional_fields and not self.required_fields:
            # simplest schema type for one field
            self.complete_optional_field_dictionaries(entries)

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
    schema_dict = Struct(**config_dict)
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
    errors = db.Column(db.Text, nullable=True)

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

schema = create_schema_from_config(order_fields['order_fields_validators'])

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
                values.update({headers[i]: item})
            # validate the row
            try:
                values = schema(values)
                
            except MultipleInvalid as e:
                
                values['valid'] = False
                values['errors'] = []
                for error in e.errors: # loops through each field in the schema that raised errors
                    print 'in loop for error with field: '
                    print error.path

                    print error.error_message
                    
               

                    #     values['errors'].append({'field':error.path[0] if error.path else error, 'errors':[err.error_message for err in error.errors]})
                    # else:
                    values['errors'].append({'field':error.path[0] if error.path else error, 'errors':error.error_message})
                    # print error.nullify
                    # print error.path[0]
                    # if hasattr(error, 'nullify') and error.nullify:
                    #     print 'trying to nullify'
                    if error.path and len(error.path) == 1:
                        field_name = error.path[0]
                        if field_name in order_fields_defaults:
                            # this is a field that requires a replacement value if type/format coercion fails
                            print error.error_message
                            print order_fields_defaults[field_name]['coerce_failure_msg']
                            if order_fields_defaults[field_name]['coerce_failure_msg'] == error.error_message:
                                # the error message corresponds to the coercion error message, update with replacement value
                                print 'setting {} to {}'.format(field_name, order_fields_defaults[field_name]['failure_value'])
                                values[field_name] = order_fields_defaults[field_name]['failure_value']
                            else:
                                # the coercion was successul but another validation requirement failed.
                                # coerce again to avoid database Type Errors

                                coerce_schema = create_schema_from_config({field_name:{'functions':{'CoerceTo':order_fields['order_fields_validators']['optional_fields'][field_name]['functions']['CoerceTo']}}})
                                print coerce_schema.schema.keys()[0]
                                values.update(coerce_schema({field_name:values[field_name]}))
                                print values[field_name]

# for item in validate.schema.keys():
#     if hasattr(item, '__call__') and item.__name__ == Coerce.__name__:
#         print item

                    #     values.update({error.path[0]:None})
                values['errors'] = str(values['errors'])
                
            # create database record
            print values['birthday']
            print type(values['birthday'])
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
