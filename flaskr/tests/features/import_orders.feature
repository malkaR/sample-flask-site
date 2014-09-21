Feature: Import Orders In Bulk
    
    Scenario Outline: Import One Valid Order
        Given I read the contents of a csv file containing an order from <file_name>
        When I do an http put request with the file string data
        Then I see the order id <id> present in the database
        Then I see the order name <name> present in the database
        Then I see the order email <email> present in the database
        Then I see the order state <state> present in the database
        Then I see the order zipcode <zipcode> present in the database
        Then I see the order birthday <birthday> present in the database
        Then I see the order validity <valid> present in the database
        Then I see the order validation failures <failures> present in the database
        Then I receive a successful status code of 200

         

    Examples:
    	| file_name         |  id   |       name      |                    email                   | state |  zipcode |   birthday   | valid |             failures             |
    	| OneValidOrder.csv |  2499 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  IA   |   05938  | Feb 27, 1963 |   1   |                None              |
        | OneInvalidOrderState.csv |  2399 | Stone Dominguez |  ligula.Aliquam.erat@semperegestasurna.com |  NJ   |   05938  | Feb 27, 1963 |   0   |    Field: state; Value: NJ; Error: This is not an allowed value    |
