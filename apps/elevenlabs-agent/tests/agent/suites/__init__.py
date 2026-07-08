"""Conversational test suites for Daisy — one module per suite.

Each module mirrors a suite in scenarios.feature (T1..T4 tiers, E edge cases,
NS needs-spec) and exposes build(save_tool_id) -> list[TestsCreateRequestBody].
Register a new suite by adding its module to SUITES in sync_tests.py.
"""
