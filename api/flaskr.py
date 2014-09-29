
from datetime import datetime, date
import os
import sys
from string import Template
import yaml

from flask import Flask
from flask.ext.restful import Api
from flask.ext.sqlalchemy import SQLAlchemy

from config.validation_constants import *
from validation.formatter import SchemaFormatter
from validation.util import *

sys.path.append(os.path.abspath(os.pardir))


from api.validation.formatter import create_schema_from_config


app = Flask(__name__)
if 'FLASKR_SETTINGS' in os.environ:
	app.config.from_envvar('FLASKR_SETTINGS', silent=True)
else:
	app.config.from_object('api.settings')
rest_api = Api(app)
db = SQLAlchemy(app)



validate_with = dict((const,eval(const)) for const in VALIDATION_CONSTANTS + VALIDATION_ERRORS)
# parse yaml validators
order_fields_file = open(os.path.abspath(os.path.join(app.config['PROJECT_DIR'], 'api/config/field_validators.yaml')))
s = Template(order_fields_file.read())
s = s.substitute(**validate_with)
# use safe_load instead load
order_fields = yaml.load(s)
order_fields_file.close()

# Order validation 
schema, dependent_schema = create_schema_from_config(order_fields['order_fields_validators'], simple=False)



import resources
# Routes


rest_api.add_resource(resources.OrderImport, '/orders/import/')
rest_api.add_resource(resources.Orders, '/orders/')
rest_api.add_resource(resources.FullOrder, '/orders/<string:order_id>/')






    

if __name__ == '__main__':
    app.run()
