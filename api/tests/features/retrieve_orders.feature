Feature: Retrieve All The Orders
    
    Scenario Outline: Retrieve all orders in the database
        Given I delete and recreate the database
        And I read the contents of a csv file containing orders from <file_name>
        And I do an http put request with the file string data
        When I do an http get request for all the orders in the database
        Then I receive a successful status code of 200
        Then the response has a content type of application/json
        Then the results list in the response contains <number> items
        Then each item in the results list contains the expected resource fields
        Then each of the result items's values match the database record's values
        

    Examples:
        | file_name                | number |
        | OneValidOrder.csv        |    1   |
        | OneInvalidOrderState.csv |    1   |
        | TwoValidOrders.csv       |    2   |
        | TwoInvalidOrders.csv     |    2   |
        | TwoValidOrdersSamePrimaryKey.csv     |    1   |