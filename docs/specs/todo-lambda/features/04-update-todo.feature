@slice-04 @integration
Feature: Update Todo (Patch)
  As a client of the Todo API
  I want to partially update a todo
  So that I can change only the fields I care about

  Background:
    Given an existing todo titled "Buy milk" with description "2% milk" and completed false

  Scenario: Patching only the title
    When a client patches that todo with title "Buy oat milk"
    Then the response is 200 OK
    And the response body is a todo with title "Buy oat milk", description "2% milk", completed false
    And updatedAt is refreshed

  Scenario: Patching only completed
    When a client patches that todo with completed true
    Then the response is 200 OK
    And the response body is a todo with title "Buy milk", completed true

  Scenario: Patching multiple fields at once
    When a client patches that todo with title "Buy oat milk" and completed true
    Then the response is 200 OK
    And the response body is a todo with title "Buy oat milk", completed true

  Scenario: Rejecting an empty patch body
    When a client patches that todo with no fields
    Then the response is 422 Unprocessable Content
    And the todo is unchanged

  Scenario: Rejecting a patch with only unknown fields
    When a client patches that todo supplying only an id and a createdAt of their own choosing
    Then the response is 422 Unprocessable Content
    And the todo is unchanged

  Scenario: Rejecting an invalid title on patch
    When a client patches that todo with title "   "
    Then the response is 422 Unprocessable Content
    And the todo is unchanged

  Scenario: Rejecting a title over the length limit on patch
    When a client patches that todo with a title of 201 characters
    Then the response is 422 Unprocessable Content
    And the todo is unchanged

  Scenario: Server-only fields are ignored on patch
    When a client patches that todo with title "Buy oat milk", supplying an id, createdAt, and updatedAt of their own choosing
    Then the response is 200 OK
    And the response body is a todo with title "Buy oat milk"
    And the response body's createdAt is unchanged from before the patch

  Scenario: Patching a todo that does not exist
    When a client patches a todo by an id that does not exist, with title "Anything"
    Then the response is 404 Not Found
