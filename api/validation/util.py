"""Custom function validators for use with the voluptuous library"""
from validate_email import validate_email
from voluptuous import Length,  Invalid

import sys, os 
sys.path.append(os.path.abspath(os.pardir))
from api.config.validation_constants import *

from datetime import date, datetime

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







