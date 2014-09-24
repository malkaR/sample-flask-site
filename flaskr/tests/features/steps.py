import os
import sys
import json
sys.path.append(os.path.abspath(os.pardir))
from datetime import date
from lettuce import * 
from flaskr import (Order, basic_resource_fields, LENGTH_ERRROR, FORBIDDEN_VALUE_ERROR, AT_MOST_DATE_RANGE_ERROR, get_base_error_message,
        LOWER_THAN_DATE_RANGE_ERROR, HIGHER_THAN_DATE_RANGE_ERROR, AT_LEAST_DATE_RANGE_ERROR, COERCE_DATE_ERROR)
from terrain import init_db

# --------- Steps to prepare data fixtures --------- #

@step('I delete and recreate the database')
def tear_down_and_set_up(step):
    init_db()

@step('I read the contents of a csv file containing an order from (\w+.csv)')
def have_the_data_file(step, file_name):
    world.file_data = open('data/' + file_name, 'rb').read()

# --------- Steps to verify basic request/response behaviors --------- #

@step('I do an http put request with the file string data')
def do_an_http_put_request(step):
    world.response = world.app.put('/orders/import', data=dict(
        data=world.file_data
    )) 

@step('I do an http get request for all the orders in the database')
def do_an_http_get_request(step):
    world.response = world.app.get('/orders')  
    
@step('I receive a successful status code of (\d+)')
def check_status_code(step, expected):
    expected = int(expected)
    assert world.response.status_code == expected, \
        "Got %d" % world.response.status_code

@step('the response has a content type of (.*)')
def check_content_type(step, expected):
    assert world.response.headers['content-type'] == expected, \
        "Got %s" % world.response.headers['content-type']

# --------- Steps to use when one record exists --------- #

@step('I see the order id (\d+) present in the database')
def check_order_id(step, expected):
    expected = int(expected)
    order = world.db.session.query(Order).first()
    assert order.id == expected, \
        "Got %d" % order.id

@step('I see the order name ([\w\s]+) present in the database')
def check_order_name(step, expected):
    order = world.db.session.query(Order).first()
    assert order.name == expected, \
        "Got %s" % order.name

@step('I see the order email (.*) present in the database')
def check_order_email(step, expected):
    order = world.db.session.query(Order).first()
    assert order.email == expected, \
        "Got %s" % order.email

@step('I see the order state (\w{2}) present in the database')
def check_order_state(step, expected):
    order = world.db.session.query(Order).first()
    assert order.state == expected, \
        "Got %s" % order.state

@step('I see the order zipcode (\w*) present in the database')
def check_order_zipcode(step, expected):
    order = world.db.session.query(Order).first()
    assert order.zipcode == expected, \
        "Got %s" % order.zipcode

@step('I see the order birthday (.*) present in the database')
def check_order_birthday(step, expected):
    order = world.db.session.query(Order).first()
    assert date.strftime(order.birthday, '%b %d, %Y') == expected, \
        "Got %s" % order.birthday  

@step('I see the order validity (.*) present in the database')
def check_order_validity(step, expected):
    expected = bool(int(expected))
    order = world.db.session.query(Order).first()
    assert order.valid == expected, \
        "Got %s, errors found %s" % (order.valid, order.errors)

@step('I see the order validation errors (.*) present in the database')
def check_order_errors(step, expected):
    order = world.db.session.query(Order).first()
    if expected == 'None':
        expected = None
        assert order.errors == expected, \
            "Got %s" % order.errors  
    else:
        expected = expected.split(',')
        order_errors = list(order.errors)
        for error in expected:
            error_msg = get_base_error_message(error)
            assert error_msg in order.errors, \
                "Got %s, missing %s" % (order.errors, error_msg)


# --------- Steps to use when multiple records exist --------- #

@step('the results list in the response contains (\d+) items')
def check_result_length(step, expected):
    expected = int(expected)
    results = json.loads(world.response.get_data())['results']
    assert len(results) == expected, \
        "Got %d results" % len(results)

@step('each item in the results list contains the expected resource fields')
def check_basic_fields_present(step):
    results = json.loads(world.response.get_data())['results']
    for field in basic_resource_fields.keys():
        for result_dict in results:
            assert field in result_dict, \
                "Got result dictionary: %s, missing the field %s" % (str(result_dict), field)

@step('each of the result items\'s values match the database record\'s values')
def check_values_match_to_database(step):
    results = json.loads(world.response.get_data())['results']
    for result_dict in results:
        order = world.db.session.query(Order).filter_by(id=result_dict['id']).first()
        
        for field in [f for f in basic_resource_fields.keys() if f != 'id']:
            assert getattr(order, field) == result_dict[field], \
                "Got %s, expected %s" % (result_dict[field], getattr(order, field))





