@slice-03 @integration
Feature: List Todos
  As a client of the Todo API
  I want to list todos with filtering and pagination
  So that I can browse the list without fetching everything at once

  Background:
    Given the following todos exist, oldest first:
      | title        | completed |
      | Buy milk     | false     |
      | Walk the dog | true      |
      | Pay rent     | false     |

  Scenario: Listing todos defaults to newest-first
    When a client lists todos with no parameters
    Then the response is 200 OK
    And the response body is a paginated envelope of todos in order: "Pay rent", "Walk the dog", "Buy milk"

  Scenario: Filtering by completed
    When a client lists todos with completed filter "true"
    Then the response is 200 OK
    And the response body is a paginated envelope containing only "Walk the dog"

  Scenario: Filtering by incomplete
    When a client lists todos with completed filter "false"
    Then the response is 200 OK
    And the response body is a paginated envelope containing only "Pay rent" and "Buy milk", newest-first

  Scenario: Paginating with a limit smaller than the total
    When a client lists todos with limit 2
    Then the response is 200 OK
    And the response body contains exactly 2 todos and a non-null nextCursor
    When a client lists todos using that nextCursor
    Then the response body contains the remaining todo and a null nextCursor

  Scenario Outline: Rejecting invalid pagination or filter parameters
    When a client lists todos with <parameter>
    Then the response is 422 Unprocessable Content

    Examples:
      | parameter                   |
      | limit "0"                   |
      | limit "101"                 |
      | limit "not-a-number"        |
      | cursor "not-a-real-cursor"  |
      | completed filter "maybe"    |
