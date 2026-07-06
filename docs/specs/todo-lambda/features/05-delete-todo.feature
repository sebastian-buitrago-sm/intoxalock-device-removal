@slice-05 @integration
Feature: Delete Todo
  As a client of the Todo API
  I want to delete a todo
  So that it no longer appears in the list or is fetchable by id

  Background:
    Given an existing todo titled "Buy milk"

  Scenario: Deleting an existing todo
    When a client deletes that todo
    Then the response is 204 No Content
    When a client fetches that todo by id
    Then the response is 404 Not Found

  Scenario: Deleting a todo that does not exist
    When a client deletes a todo by an id that does not exist
    Then the response is 404 Not Found

  Scenario: Deleting a todo twice
    Given that todo has already been deleted
    When a client deletes that todo again
    Then the response is 404 Not Found
