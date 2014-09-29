Feature: Import Orders In Bulk
    
    Scenario Outline: Import Several Orders and Validate Them
        Given I delete and recreate the database
        And I read the contents of a csv file containing orders from <file_name>
        When I do an http put request with the file string data
        Then I receive a successful status code of 200
        Then I see the list of order ids <id_list> present in the database
        Then for each order in the <id_list> I verify the name fields in <name_list> are correct
        Then for each order in the <id_list> I verify the email fields in <email_list> are correct
        Then for each order in the <id_list> I verify the state fields in <state_list> are correct
        Then for each order in the <id_list> I verify the zipcode fields in <zipcode_list> are correct
        Then for each order in the <id_list> I verify the birthday fields in <birthday_list> are correct
        Then for each order in the <id_list> I verify the valid fields in <valid_list> are correct
        Then for each order in the <id_list> I verify the errors fields in <errors_list> are correct
         

    Examples:
        |      file_name     |    id_list      |            name_list         |     email_list    |  state_list  |     zipcode_list    |      birthday_list      | valid_list    | errors_list    |
        | TwoValidOrders.csv |  [3887; 39702]  | [Stone Dominguez; Davis Walters] |  [ligula.Aliquam.erat@semperegestasurna.com; euismod@sit.edu]   |   [NY; KS]    |   [13234; 67102]   |  [Feb 27, 1963; Mar 21, 1941]  |  [1; 1]    |   [None; None]   | 
