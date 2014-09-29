Feature: Import One Order
    
    Scenario Outline: Import One Order and Validate It
        Given I delete and recreate the database
        And I read the contents of a csv file containing orders from <file_name>
        When I do an http put request with the file string data
        Then I see the order id <id> present in the database
        Then I see the order name <name> present in the database
        Then I see the order email <email> present in the database
        Then I see the order state <state> present in the database
        Then I see the order zipcode <zipcode> present in the database
        Then I see the order birthday <birthday> present in the database
        Then I see the order validity <valid> present in the database
        Then I see the order validation errors <errors> present in the database
        Then I receive a successful status code of 201

         

    Examples:
        | file_name         |  id   |       name      |                    email                   | state |  zipcode |   birthday   | valid |             errors             |
        | OneValidOrder.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  IA   |   40302  | Feb 27, 1963 |   1   |                None              |
        | OneInvalidOrderNYStateDotNetEmail.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.net |  NY   |   40302  | Feb 27, 1963 |   0   |    NY_EMAIL_ERROR   | 
        | OneOrderInvalidBirthdayFormat.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  NY   |   80081  | None |   0   |    COERCE_DATE_ERROR   |
        | OneOrderInvalidBirthdayRange.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  NY   |   80081  | Feb 27, 1995 |   0   |     AT_MOST_DATE_RANGE_ERROR      |
        | OneInvalidOrderState.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  NJ   |   40302  | Feb 27, 1963 |   0   |    FORBIDDEN_VALUE_ERROR   |        
        | OneOrderInvalidZipcodeLength.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  NY   |   8440212  | Feb 27, 1963 |   0   |    LENGTH_CHOICE_ERROR_ZIPCODE   |
        | OneOrderInvalidZipcodeType.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  NY   |   None  | Feb 27, 1963 |   0   |    COERCE_INT_ERROR   |
        | OneOrderInvalidZipcodeInvalidState.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  NJ   |   8959381  | Feb 27, 1963 |   0   |    FORBIDDEN_VALUE_ERROR, LENGTH_CHOICE_ERROR    |
        | OneInvalidOrderEmail.csv |  2499 | Stone Dominguez |  ligula.Aliquam.eratsemperegestasurna.com |  NY   |   40302  | Feb 27, 1963 |   0   |    INVALID_EMAIL_ERROR   |     
        | OneOrderInvalidZipcodeSum.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  IA   |   15938  | Feb 27, 1963 |   0   |       SUM_MAX_ERROR      |  




