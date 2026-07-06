@slice-02 @integration
Feature: Get Todo by id
  As a client of the Todo API
  I want to fetch a single todo by id
  So that I can see its current state

  Background:
    Given an existing todo titled "Buy milk"

  Scenario: Fetching an existing todo
    When a client fetches that todo by id
    Then the response is 200 OK
    And the response body is the todo titled "Buy milk"

  Scenario: Fetching a todo that does not exist
    When a client fetches a todo by an id that does not exist
    Then the response is 404 Not Found
    And the response is a problem response
