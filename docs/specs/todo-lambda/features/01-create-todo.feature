@slice-01 @integration
Feature: Create Todo
  As a client of the Todo API
  I want to create a todo
  So that it is persisted and returned with server-assigned metadata

  Scenario: Create a todo with only a title
    When a client creates a todo with title "Buy milk"
    Then the response is 201 Created
    And the response has a Location header pointing to the created todo
    And the response body is a todo with title "Buy milk", no description, completed false, a generated id, and timestamps

  Scenario: Create a todo with title and description
    When a client creates a todo with title "Buy milk" and description "2% and oat milk"
    Then the response is 201 Created
    And the response body is a todo with title "Buy milk", description "2% and oat milk", and completed false

  Scenario: Title is trimmed before validation
    When a client creates a todo with title "  Buy milk  "
    Then the response is 201 Created
    And the response body is a todo with title "Buy milk"

  Scenario: Rejecting a missing title
    When a client creates a todo without a title
    Then the response is 422 Unprocessable Content
    And no todo is persisted

  Scenario: Rejecting an empty title
    When a client creates a todo with title ""
    Then the response is 422 Unprocessable Content
    And no todo is persisted

  Scenario: Rejecting a whitespace-only title
    When a client creates a todo with title "   "
    Then the response is 422 Unprocessable Content
    And no todo is persisted

  Scenario: Rejecting a title over the length limit
    When a client creates a todo with a title of 201 characters
    Then the response is 422 Unprocessable Content
    And no todo is persisted

  Scenario: Rejecting a description over the length limit
    When a client creates a todo with title "Buy milk" and a description of 2001 characters
    Then the response is 422 Unprocessable Content
    And no todo is persisted

  Scenario: Server-only fields are ignored on create
    When a client creates a todo with title "Buy milk", supplying an id, createdAt, updatedAt, and completed of their own choosing
    Then the response is 201 Created
    And the response body is a todo with title "Buy milk", completed false
    And the response body's id, createdAt, and updatedAt differ from the client-supplied values
