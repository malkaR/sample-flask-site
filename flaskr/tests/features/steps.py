import os
import sys
sys.path.append(os.path.abspath(os.pardir))
from lettuce import * 
from flaskr import Order

@step('I read the contents of a csv file containing orders from (\w+.csv)')
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

@step('I receive a successful status code of (\d+)')
def check_status_code(step, expected):
    expected = int(expected)
    assert world.put_response.status_code == expected, \
        "Got %d" % world.put_response.status_code

