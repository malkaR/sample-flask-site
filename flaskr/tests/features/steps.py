import os
import sys
sys.path.append(os.path.abspath(os.pardir))
from datetime import date
from lettuce import * 
from flaskr import Order
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

@step('I see the order zipcode (\d{5}) present in the database')
def check_order_zipcode(step, expected):
    expected = int(expected)
    order = world.db.session.query(Order).first()
    assert order.zipcode == expected, \
        "Got %d" % order.zipcode

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
        "Got %s" % order.valid   

@step('I see the order validation failures (.*) present in the database')
def check_order_failures(step, expected):
    order = world.db.session.query(Order).first()
    if expected == 'None':
        expected = None
        assert order.failures == expected, \
            "Got %s" % order.failures  
    else:
        assert expected in order.failures, \
            "Got %s" % order.failures




# --------- Steps to use when multiple records exist --------- #
        # The the results list in the response contains 3 items
        # Then each item in the results list match the expected resource fields
        # Then the result items values match the database record values

        # The the results list in the response contains 3 items
        # Then each item in the results list match the expected resource fields
        # Then the result items values match the database record values

