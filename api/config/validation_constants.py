import us
from datetime import date, datetime

# allowed, required, or forbidden values and formats
US_STATES = [state.abbr for state in us.states.STATES]
STATES_LESS_NY = [str(state.abbr) for state in us.states.STATES if state.abbr != 'NY']
DATE_FORMAT = '%b %d, %Y'
today = date.today()
ZIPCODE_LENGTHS = [5, 9]
TODAY_LESS_21_YEARS = date(year=today.year - 21, month = today.month, day=today.day)
FORBIDDEN_STATES = ['NJ', 'CT', 'PA', 'MA', 'OR', 'ID', 'IL']
MAX_ZIPCODE_SUM = 20

VALIDATION_CONSTANTS = ['US_STATES',
						'STATES_LESS_NY', 
						'DATE_FORMAT', 
						'ZIPCODE_LENGTHS', 
						'TODAY_LESS_21_YEARS', 
						'FORBIDDEN_STATES', 
						'MAX_ZIPCODE_SUM']

# validation error messages
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
LENGTH_CHOICE_ERROR_ZIPCODE = LENGTH_CHOICE_ERROR.format(ZIPCODE_LENGTHS)

VALIDATION_ERRORS = ['LENGTH_CHOICE_ERROR',
					'LENGTH_RANGE_ERROR',
					'SUM_MAX_ERROR',
					'FORBIDDEN_VALUE_ERROR',
					'AT_MOST_DATE_RANGE_ERROR',
					'LOWER_THAN_DATE_RANGE_ERROR',
					'HIGHER_THAN_DATE_RANGE_ERROR',
					'AT_LEAST_DATE_RANGE_ERROR',
					'COERCE_DATE_ERROR',
					'COERCE_INT_ERROR',
					'INVALID_EMAIL_ERROR',
					'NY_EMAIL_ERROR',
					'MISSING_ENDING_ERROR',
					'UNALLOWED_ENDING_ERROR',
					'LENGTH_CHOICE_ERROR_ZIPCODE']
