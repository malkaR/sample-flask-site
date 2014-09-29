from voluptuous import Schema, Required, All, Length, Range, Error, MultipleInvalid, Invalid, Any, Match, In

from util import *

class SchemaFormatter:
    """Convert values from a dictionary to a valid voluptuous schema"""
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
        """Add required fields to the schema"""
        for field_name, field_validators in required_field_dict.items():
            self.schema[Required(field_name)] = self.create_schema_from_args(self.get_field_validators(field_validators))

    def complete_optional_field_dictionaries(self, optional_field_dict):
        """Add optional fields to the schema"""
        for field_name, field_validators in optional_field_dict.items():
            self.schema[field_name] = self.create_schema_from_args(self.get_field_validators(field_validators))

    def complete_dependent_fields_dictionaries(self, dependent_fields_dict):
        """
        Formats a schema to specify a validation rule that depends on more than one field.
        The dictionary must have a qualifier such as 'Any' or 'All'.
        Additional dictionary keys can be 'Or', 'And', or field names.
        The second level dictionary can have the logical opposite of the key previosly used (And if Or was used, Or
        if And was used) and any additional field names.
        Field names are processed like any other schema for a field.
        """

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
            self.dependent_schema = self.create_schema_from_args(top_level_args, qualifier=qualifier, msg=msg, extra=True)
        elif top_level_dict:
            self.dependent_schema = self.create_schema_from_args([top_level_dict], qualifier=qualifier, msg=msg, extra=True)
            
    def get_field_validators(self, field_validators):
        """
        Each field in the schema can specify a python type, a literal value, or any number of functions.
        """
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
        """
        Apply a qualifier to a list of arguments to create a schema for one field.
        """
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
    """Wrapper function to create and return the schema from the config dictionary"""
    schema_dict = SchemaFormatter(**config_dict)
    if simple:
        return Schema(schema_dict.get_schema())
    return [Schema(schema_dict.get_schema(), extra=True), Schema(schema_dict.get_dependent_schema())]

