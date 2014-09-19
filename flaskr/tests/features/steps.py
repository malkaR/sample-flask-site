import os
import sys
sys.path.append(os.path.abspath(os.pardir))
from datetime import date
from lettuce import * 
from flaskr import Order

@step('I read the contents of a csv file containing an order from (\w+.csv)')
def have_the_data_file(step, file_name):
    world.file_data = open('data/' + file_name, 'rb').read()

@step('I do an http put request with the file string data')
def do_an_http_put_request(step):
    world.put_response = world.app.put('/', data=dict(
        data=world.file_data
    )) 

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
        
@step('I receive a successful status code of (\d+)')
def check_status_code(step, expected):
    expected = int(expected)
    assert world.put_response.status_code == expected, \
        "Got %d" % world.put_response.status_code

