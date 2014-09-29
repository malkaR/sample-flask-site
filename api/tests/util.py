"""Utility functions for tests"""
from config.validation_constants import *

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