Feature: Retrieve All The Orders
    
    Scenario Outline: Retrieve all orders in the database
        Given I delete and recreate the database
        And I read the contents of a csv file containing an order from <file_name>
        And I do an http put request with the file string data
        When I do an http get request for all the orders in the database
        Then I receive a successful status code of 200
        Then the response has a content type of application/json
        
         

    Examples:
        | file_name         | 
        | OneValidOrder.csv |
        | OneInvalidOrderState.csv | 